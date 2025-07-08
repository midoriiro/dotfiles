from contextlib import contextmanager
import logging
from pathlib import Path
import shutil
import sys
import sysconfig
from typing import Any, Generator, Optional, Tuple, override
import zipfile
from poetry.core.poetry import Poetry

from poexy_core.builders.builder import PythonTag
from poexy_core.builders.wheel import Manifests, WheelBuilder, WheelMetadata
from poexy_core.metadata.fields import MetadataField
from poexy_core.pyinstaller.builder import BuildType, PyinstallerBuilder
from poexy_core.packages.files import WHEEL_EXTENSIONS
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class BinaryBuilder(WheelBuilder):
    def __init__(
            self,
            poetry: Poetry,
            poexy: Poexy,
            format: PackageFormat,
            wheel_directory: Path | None = None,
            metadata_directory: Path | None = None,
            config_settings: dict[str, Any] | None = None,
        ):
        if format != PackageFormat.Binary:
            raise ValueError(f"Invalid format: {format}")
        super().__init__(
            poetry,
            poexy,
            PackageFormat.Wheel,
            wheel_directory,
            metadata_directory,
            config_settings
        )
        python_tag = PythonTag.from_current_environment()
        self._init_metadata(python_tag)
        self._manifests = Manifests(self._metadata.dist_info_folder)

    def __add_files(self, executable: Tuple[Path, Path]):
        def add_file(source: Path, destination: Path):
            logger.info(f"Recording file: {destination}")
            self._manifests.record.set(source, destination)

        def predicate(path: Path) -> Optional[Path]:
            if path.suffix not in WHEEL_EXTENSIONS:
                return self._metadata.data_data_folder
            return False

        add_file(
            executable[0],
            executable[1]
        )

        self._add_files(
            predicate,
            add_file
        )

    @override
    def _add_wheel(self):
        self._manifests.wheel.set("Wheel-Version", "1.0")
        self._manifests.wheel.set("Generator", "Poexy")
        self._manifests.wheel.set("Root-Is-Purelib", "false")
        self._manifests.wheel.set("Tag", f"{self._metadata.python_tag}")

    @override
    def _add_metadata(self):
        builder = super()._add_metadata(self._manifests.metadata)
        classifiers = list(builder.get(MetadataField.Classifier))
        classifiers = [c for c in classifiers if not c.startswith("Programming Language :: Python ::")]
        builder.delete(MetadataField.Classifier)
        classifiers.append(f"Programming Language :: Python :: {sys.version_info.major}.{sys.version_info.minor}")
        classifiers.append("Operating System :: OS Independent")
        builder.set(MetadataField.Classifier, classifiers)
        fields_to_delete = [
            MetadataField.RequiresDist,
            MetadataField.RequiresExternal,
            MetadataField.RequiresPython,
            MetadataField.ProvidesExtra,
            MetadataField.ProvidesDist,
            MetadataField.SupportedPlatforms,
        ]
        for field in fields_to_delete:
            try:
                builder.delete(field)
            except KeyError:
                pass
        return builder

    def prepare(self) -> Path:
        logger.info(f"Preparing wheel metadata...")
        logger.info(f"Adding metadata...")
        self._add_metadata()
        logger.info(f"Adding wheel...")
        self._add_wheel()
        logger.info(f"Writing manifests...")
        self._manifests.metadata.write()
        self._manifests.wheel.write()
        logger.info(f"Wheel metadata prepared successfully.")
        return self._metadata.dist_info_folder
    
    def build_executable(self) -> Tuple[Path, Path]:
        pyinstaller_builder = PyinstallerBuilder(
            self.poetry,
            self.poexy
        )
        logger.info(f"Building executable: {pyinstaller_builder.executable_name}")
        pyinstaller_builder.build(
            build_type=BuildType.OneFile,
            dist_path=self.destination_directory,
            strip=True,
            clean=True,
        )  
        executable_name = pyinstaller_builder.executable_name
        source = self.destination_directory / executable_name
        destination = self._metadata.data_scripts_folder / executable_name
        return source, destination
    
    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building binary...")

        executable = self.build_executable()
        logger.info("Adding metadata...")
        self._add_metadata()
        logger.info("Adding wheel...")
        self._add_wheel()
        logger.info("Adding files...")
        self.__add_files(executable)
        logger.info("Writing manifests...")
        self._manifests.write()

        self._create_archive()

        logger.info("Built successfully.")

        shutil.copy(self._metadata.archive_path, self.destination_directory)

        yield self._metadata.archive_path
       
    