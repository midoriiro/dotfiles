import logging
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, override

from poetry.core.poetry import Poetry

from poexy_core.builders.builder import PythonTag
from poexy_core.builders.hooks.include_files import IncludeFilesHookBuilder
from poexy_core.builders.hooks.license import LicenseHookBuilder
from poexy_core.builders.wheel import Manifests, WheelBuilder
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class EditableBuilder(WheelBuilder):
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
        super().__init__(
            poetry,
            poexy,
            _format,
            wheel_directory,
            metadata_directory,
            config_settings,
        )
        python_tag = PythonTag(impl="py", major=sys.version_info.major)
        self._init_metadata(python_tag)
        self._manifests = Manifests(self._metadata.dist_info_folder)

        self._hooks.clear()

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

    def __add_pth(self) -> None:
        package_name = self.poetry.package.name
        source = self.poexy.package.source.resolve().as_posix()
        source_path = self._metadata.root_folder / f"{package_name}.pth"
        logger.info(f"Adding pth file: {source_path}")
        with open(source_path, "w", encoding="utf-8") as f:
            logger.info(f"With content: {source}")
            f.write(source)
        self._add_files_to_archive(source_path, source_path)

    @override
    @contextmanager
    def build(self) -> Generator[Path, None, None]:
        logger.info("Building editable wheel...")

        for hook in self._hooks:
            hook.build()

        with self._create_archive():
            logger.info("Adding metadata...")
            self._add_metadata(self._manifests.metadata)
            logger.info("Adding wheel...")
            self._add_wheel()
            logger.info("Adding pth file...")
            self.__add_pth()
            logger.info("Writing manifests...")
            self._manifests.write()
            logger.info("Adding dist-info files...")
            self._add_dist_info_files_to_archive()

        logger.info("Built successfully.")

        shutil.copy(self._metadata.archive_path, self.destination_directory)

        yield self._metadata.archive_path
