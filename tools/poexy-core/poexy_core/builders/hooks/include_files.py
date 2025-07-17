import logging
from pathlib import Path
from typing import override

from poetry.core.masonry.metadata import Metadata

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class IncludeFilesHookBuilder(HookBuilder):
    def __init__(
        self,
        poexy: Poexy,
        _format: PackageFormat,
        destination: Path,
    ):
        super().__init__("include_files")
        self.__poexy = poexy
        self.__format = _format
        self.__destination = destination
        self.__files = []

    @override
    def build(self):
        with self._hook_build():
            logger.info("Resolving include files...")
            resolved = self.__poexy.resolve_inclusions(self.__format)
            exclusions = [file.source for file in resolved.excludes]

            logger.info(f"Resolved {len(resolved.includes)} files to include.")
            logger.info(f"Resolved {len(resolved.excludes)} files to exclude.")

            count = 0

            for file in resolved.includes:
                if file.source in exclusions:
                    logger.info(f"Excluding file: {file.source}")
                    continue
                logger.info(f"Including file: {file.source}")
                self.__files.append(
                    (file.source, self.__destination / file.destination)
                )
                count += 1

            logger.info(f"{count} files ready to be packaged.")

    @override
    def add_files(self, callback: FilePathCallback):
        with self._hook_add_files():
            for source, destination in self.__files:
                callback(source, destination)

    @override
    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        pass
