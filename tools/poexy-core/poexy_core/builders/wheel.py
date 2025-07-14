import logging
import shutil
import sys
import zipfile
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Optional, override

from packaging.utils import NormalizedName
from poetry.core.masonry.utils.helpers import distribution_name
from poetry.core.poetry import Poetry

from poexy_core.builders.builder import Builder, PythonTag
from poexy_core.builders.hooks.include_files import IncludeFilesHookBuilder
from poexy_core.builders.hooks.license import LicenseHookBuilder
from poexy_core.builders.hooks.package_files import PackageFilesHookBuilder
from poexy_core.builders.types import FilePathPredicate
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
        self.name: str = distribution_name(NormalizedName(name))
        self.version: str = version
        self.python_tag: PythonTag = python_tag
        self.archive_path: Path = self.__archive_path()
        if root_folder is None:
            self.root_folder = self.__root_folder()
        else:
            self.root_folder = root_folder
        self.dist_info_folder: Path = self.__dist_info_folder()
        self.data_purelib_folder: Path = self.__data_folder(WheelDataScheme.PURELIB)
        self.data_platlib_folder: Path = self.__data_folder(WheelDataScheme.PLATLIB)
        self.data_headers_folder: Path = self.__data_folder(WheelDataScheme.HEADERS)
        self.data_scripts_folder: Path = self.__data_folder(WheelDataScheme.SCRIPTS)
        self.data_data_folder: Path = self.__data_folder(WheelDataScheme.DATA)

    def __archive_path(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}-{self.python_tag}.whl")

    def __root_folder(self) -> Path:
        return self.path / Path(f"{self.name}-{self.version}")

    def __dist_info_folder(self) -> Path:
        return self.root_folder / Path(f"{self.name}-{self.version}.dist-info")

    def __data_folder(self, scheme: WheelDataScheme) -> Path:
        return (
            self.root_folder / Path(f"{self.name}-{self.version}.data") / scheme.value
        )


class WheelBuilder(Builder):
    def __init__(
        self,
        poetry: Poetry,
        poexy: Poexy,
        _format: PackageFormat,
        wheel_directory: Path,
        metadata_directory: Path | None = None,
        config_settings: dict[str, Any] | None = None,
    ):
        if _format != PackageFormat.Wheel:
            raise ValueError(f"Invalid format: {_format}")
        super().__init__(poetry, poexy, _format, wheel_directory, config_settings)
        self._metadata_directory = metadata_directory
        python_tag = PythonTag(impl="py", major=sys.version_info.major)
        self._init_metadata(python_tag)
        self._manifests = Manifests(self._metadata.dist_info_folder)
        self.__archive: Optional[zipfile.ZipFile] = None

        self._hooks.append(
            PackageFilesHookBuilder(
                self.poexy, self.format, self.__filter_file_destination_path()
            )
        )
        self._hooks.append(
            IncludeFilesHookBuilder(
                self.poexy, self.format, self._metadata.data_data_folder
            )
        )
        self._hooks.append(
            LicenseHookBuilder(
                self.poexy,
                self._metadata.dist_info_folder / "licenses",
            )
        )

    def _init_metadata(self, python_tag: PythonTag):
        package_name = self.poetry.package.name
        package_version = str(self.poetry.package.version)
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
            root_folder,
        )

    def __filter_file_destination_path(self) -> FilePathPredicate:
        pure_lib_extensions = ".py"
        platform_lib_extensions = set(WHEEL_EXTENSIONS)

        def predicate(path: Path) -> Optional[Path]:
            if path.suffix in pure_lib_extensions:
                return self._metadata.data_purelib_folder
            if path.suffix in platform_lib_extensions:
                return self._metadata.data_platlib_folder
            if path.suffix not in WHEEL_EXTENSIONS:
                return self._metadata.data_data_folder
            return None

        return predicate

    def _add_files(self):
        def add_file(source: Path, destination: Path):
            logger.info(f"Recording file: {destination.name}")
            self._manifests.record.set(source, destination)
            self._add_files_to_archive(source, destination)

        for hook in self._hooks:
            hook.add_files(add_file)

    def _add_wheel(self):
        self._manifests.wheel.set("Wheel-Version", "1.0")
        self._manifests.wheel.set("Generator", "Poexy")
        self._manifests.wheel.set("Root-Is-Purelib", "true")
        self._manifests.wheel.set("Tag", f"{self._metadata.python_tag}")

    @contextmanager
    def _create_archive(self) -> Generator[None, None, None]:
        logger.info(
            "Creating archive: "
            f"{self._metadata.archive_path.relative_to(self._metadata.path)}"
        )
        self.__archive = zipfile.ZipFile(
            self._metadata.archive_path, "w", zipfile.ZIP_DEFLATED
        )
        yield
        self.__archive.close()
        self.__archive = None

    def _add_files_to_archive(self, source: Path, destination: Path):
        if self.__archive is None:
            raise ValueError("Archive not created")
        relative_path = destination.relative_to(self._metadata.root_folder)
        logger.info(f"Adding: {relative_path}")
        self.__archive.write(source, relative_path)

    def _add_dist_info_files_to_archive(self):
        if self.__archive is None:
            raise ValueError("Archive not created")
        self._add_files_to_archive(
            self._manifests.metadata.path, self._manifests.metadata.path
        )
        self._add_files_to_archive(
            self._manifests.wheel.path, self._manifests.wheel.path
        )
        self._add_files_to_archive(
            self._manifests.record.path, self._manifests.record.path
        )

    def prepare(self) -> Path:
        logger.info("Preparing wheel metadata...")
        logger.info(f"Metadata directory: {self._metadata.dist_info_folder}")
        logger.info("Adding metadata...")
        self._add_metadata(self._manifests.metadata)
        logger.info("Adding wheel...")
        self._add_wheel()
        logger.info("Writing manifests...")
        self._manifests.metadata.write()
        self._manifests.wheel.write()
        logger.info("Wheel metadata prepared successfully.")
        return self._metadata.dist_info_folder

    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building wheel...")

        for hook in self._hooks:
            hook.build()

        with self._create_archive():
            logger.info("Adding metadata...")
            self._add_metadata(self._manifests.metadata)
            logger.info("Adding wheel...")
            self._add_wheel()
            logger.info("Adding files...")
            self._add_files()
            logger.info("Writing manifests...")
            self._manifests.write()
            logger.info("Adding dist-info files...")
            self._add_dist_info_files_to_archive()

        logger.info("Built successfully.")

        shutil.copy(self._metadata.archive_path, self.destination_directory)

        yield self._metadata.archive_path
