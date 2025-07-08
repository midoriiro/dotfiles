from contextlib import contextmanager
from enum import Enum
import logging
from pathlib import Path
import shutil
import sys
from typing import Any, Generator, List, Optional, override
import zipfile
from poetry.core.poetry import Poetry
from poetry.core.masonry.utils.helpers import distribution_name

from poexy_core.builders.builder import Builder, PythonTag
from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.manifest.manifest import MetadataManifest, RecordManifest, WheelManifest
from poexy_core.packages.files import WHEEL_EXTENSIONS
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)

class Manifests:
    def __init__(self, path: Path):
        self.metadata: MetadataManifest = MetadataManifest(path)
        self.wheel: WheelManifest = WheelManifest(path)
        self.record: RecordManifest = RecordManifest(path)
    
    def write(self):
        self.metadata.write()
        self.wheel.write()
        self.record.add(self.metadata.path)
        self.record.add(self.wheel.path)
        self.record.add_self()
        self.record.write()


class WheelDataScheme(str, Enum):
    PURELIB = "purelib"
    PLATLIB = "platlib"
    HEADERS = "headers"
    SCRIPTS = "scripts"
    DATA = "data"


class WheelMetadata:
    def __init__(
        self,
        path: Path,
        name: str,
        version: str,
        python_tag: PythonTag,
        root_folder: Path | None = None,
    ):
        self.path: Path = path
        self.name: str = distribution_name(name)
        self.version: str = version
        self.python_tag: PythonTag = python_tag
        self.archive_path: Path = self.__archive_path()
        if root_folder is None:
            self.root_folder: Path = self.__root_folder()
        else:
            self.root_folder: Path = root_folder
        self.dist_info_folder: Path = self.__dist_info_folder()
        self.data_purelib_folder: Path = self.__data_folder(WheelDataScheme.PURELIB)
        self.data_platlib_folder: Path = self.__data_folder(WheelDataScheme.PLATLIB)
        self.data_headers_folder: Path = self.__data_folder(WheelDataScheme.HEADERS)
        self.data_scripts_folder: Path = self.__data_folder(WheelDataScheme.SCRIPTS)
        self.data_data_folder: Path = self.__data_folder(WheelDataScheme.DATA)

    def __archive_path(self) -> Path:
        """Generate the wheel filename based on package name, version and platform tag."""
        return self.path / Path(f"{self.name}-{self.version}-{self.python_tag}.whl")
    
    def __root_folder(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}")

    def __dist_info_folder(self) -> Path:
        return self.root_folder / Path(f"{self.name}-{self.version}.dist-info")
    
    def __data_folder(self, scheme: WheelDataScheme) -> Path:
        return self.root_folder / Path(f"{self.name}-{self.version}.data") / scheme.value

class WheelBuilder(Builder):
    def __init__(
            self,
            poetry: Poetry,
            poexy: Poexy,
            format: PackageFormat,
            wheel_directory: Path | None = None,
            metadata_directory: Path | None = None,
            config_settings: dict[str, Any] | None = None,
        ):
        if format != PackageFormat.Wheel:
            raise ValueError(f"Invalid format: {format}")
        super().__init__(
            poetry,
            poexy,
            format,
            wheel_directory,
            config_settings
        )
        self._metadata_directory = metadata_directory
        python_tag = PythonTag(
            impl="py",
            major=sys.version_info.major
        )
        self._init_metadata(python_tag)
        self._manifests = Manifests(self._metadata.dist_info_folder)
        self.__hooks: List[HookBuilder] = []

    def _init_metadata(self, python_tag: PythonTag):
        package_name = self.poetry.package.name
        package_version = self.poetry.package.version
        if self._metadata_directory is not None:
            destination_directory = self._metadata_directory
            root_folder = self._metadata_directory
        else:
            destination_directory = self.temp_destination_directory
            root_folder = None
        self._metadata = WheelMetadata(
            destination_directory, 
            package_name, 
            package_version, 
            python_tag,
            root_folder
        )

    def add_hook(self, hook: HookBuilder):
        self.__hooks.append(hook)

    def __add_files(self):
        pure_lib_extensions = ".py"
        platform_lib_extensions = set(WHEEL_EXTENSIONS)

        def add_file(source: Path, destination: Path):
            logger.info(f"Recording: {destination.relative_to(predicate(destination))}")
            self._manifests.record.set(source, destination)

        def predicate(path: Path) -> Optional[Path]:
            if path.suffix is None or path.suffix == "":
                if path.is_relative_to(self._metadata.data_scripts_folder):
                    return self._metadata.data_scripts_folder
                else:
                    return None
            if path.suffix in pure_lib_extensions:
                return self._metadata.data_purelib_folder
            if path.suffix in platform_lib_extensions:
                return self._metadata.data_platlib_folder
            if path.suffix not in WHEEL_EXTENSIONS:
                return self._metadata.data_data_folder
            return None
        
        for hook in self.__hooks:
            hook.add_files(add_file)

        self._add_files(
            predicate,
            add_file
        )

    def _add_wheel(self):
        self._manifests.wheel.set("Wheel-Version", "1.0")
        self._manifests.wheel.set("Generator", "Poexy")
        self._manifests.wheel.set("Root-Is-Purelib", "true")
        self._manifests.wheel.set("Tag", f"{self._metadata.python_tag}")

    def _create_archive(self):
        logger.info(f"Creating archive: {self._metadata.archive_path.relative_to(self._metadata.path)}")
        
        with zipfile.ZipFile(self._metadata.archive_path, 'w', zipfile.ZIP_DEFLATED) as wheel_zip:
            dist_info_files = []
            files = []

            def add_file(path: Path, relative_path: Path):
                logger.info(f"Adding: {relative_path}")
                wheel_zip.write(path, relative_path)
            
            for path in self._metadata.root_folder.rglob('*'):
                if path.is_file() and path.name != self._metadata.archive_path.name:
                    relative_path = path.relative_to(self._metadata.root_folder)
                    
                    # Skip dist-info folder files for now, we'll add them last
                    if str(relative_path.parent).endswith(self._metadata.dist_info_folder.name):
                        dist_info_files.append((path, relative_path))
                        logger.info(f"Queuing: {relative_path}")
                        continue
                    
                    files.append((path, relative_path))

            for path, relative_path in sorted(files, key=lambda x: x[1]):
                add_file(path, relative_path)
            
            # Add dist-info folder files last for optimization
            for path, relative_path in sorted(dist_info_files, key=lambda x: x[1]):
                add_file(path, relative_path)

    def prepare(self) -> Path:
        logger.info(f"Preparing wheel metadata...")
        logger.info(f"Metadata directory: {self._metadata.dist_info_folder}")
        logger.info(f"Adding metadata...")
        self._add_metadata(self._manifests.metadata)
        logger.info(f"Adding wheel...")
        self._add_wheel()
        logger.info(f"Writing manifests...")
        self._manifests.metadata.write()
        self._manifests.wheel.write()
        logger.info(f"Wheel metadata prepared successfully.")
        return self._metadata.dist_info_folder

    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building wheel...")

        for hook in self.__hooks:
            hook.build()

        logger.info("Adding metadata...")
        self._add_metadata(self._manifests.metadata)
        logger.info("Adding wheel...")
        self._add_wheel()
        logger.info("Adding files...")
        self.__add_files()
        logger.info("Writing manifests...")
        self._manifests.write()

        self._create_archive()

        logger.info("Built successfully.")

        shutil.copy(self._metadata.archive_path, self.destination_directory)

        yield self._metadata.archive_path
        
    