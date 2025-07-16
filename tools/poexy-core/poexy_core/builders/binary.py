import logging
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Tuple, override

from poetry.core.poetry import Poetry

from poexy_core.builders.builder import PythonTag
from poexy_core.builders.wheel import Manifests, WheelBuilder
from poexy_core.metadata.fields import MetadataField
from poexy_core.packages.format import PackageFormat
from poexy_core.pyinstaller.builder import BuildType, PyinstallerBuilder
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class BinaryBuilder(WheelBuilder):
    def __init__(
        self,
        poetry: Poetry,
        poexy: Poexy,
        _format: PackageFormat,
        wheel_directory: Path,
        metadata_directory: Path | None = None,
        config_settings: dict[str, Any] | None = None,
    ):
        if _format != PackageFormat.Binary:
            raise ValueError(f"Invalid format: {_format}")
        super().__init__(
            poetry,
            poexy,
            PackageFormat.Wheel,
            wheel_directory,
            metadata_directory,
            config_settings,
        )
        python_tag = PythonTag.from_current_environment()
        self._init_metadata(python_tag)
        self._manifests = Manifests(self._metadata.dist_info_folder)

    def __add_executable_file(self, executable: Tuple[Path, Path]):
        def add_file(source: Path, destination: Path):
            logger.info(f"Recording file: {destination}")
            self._manifests.record.set(source, destination)

        add_file(executable[0], executable[1])
        self._add_files_to_archive(executable[0], executable[1])

    @override
    def _add_wheel(self):
        self._manifests.wheel.set("Wheel-Version", "1.0")
        self._manifests.wheel.set("Generator", "Poexy")
        self._manifests.wheel.set("Root-Is-Purelib", "false")
        self._manifests.wheel.set("Tag", f"{self._metadata.python_tag}")

    def __add_metadata(self):
        builder = self._add_metadata(self._manifests.metadata)
        classifiers = list(builder.get(MetadataField.Classifier))
        classifiers = [
            c
            for c in classifiers
            if not c.startswith("Programming Language :: Python ::")
        ]
        builder.delete(MetadataField.Classifier)
        classifiers.append(
            " :: ".join(
                [
                    "Programming Language",
                    "Python",
                    f"{sys.version_info.major}.{sys.version_info.minor}",
                ]
            )
        )
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
        logger.info("Preparing wheel metadata...")
        logger.info("Adding metadata...")
        self.__add_metadata()
        logger.info("Adding wheel...")
        self._add_wheel()
        logger.info("Writing manifests...")
        self._manifests.metadata.write()
        self._manifests.wheel.write()
        logger.info("Wheel metadata prepared successfully.")
        return self._metadata.dist_info_folder

    def build_executable(self) -> Tuple[Path, Path]:
        pyinstaller_builder = PyinstallerBuilder(self.poetry, self.poexy)
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

        for hook in self._hooks:
            hook.build()

        with self._create_archive():
            logger.info("Adding metadata...")
            self._add_metadata(self._manifests.metadata)
            logger.info("Adding wheel...")
            self._add_wheel()
            logger.info("Adding executable...")
            self.__add_executable_file(executable)
            logger.info("Writing manifests...")
            self._manifests.write()
            logger.info("Adding dist-info files...")
            self._add_dist_info_files_to_archive()

        logger.info("Built successfully.")

        shutil.copy(self._metadata.archive_path, self.destination_directory)

        yield self._metadata.archive_path
