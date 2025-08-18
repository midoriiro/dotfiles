import logging
from pathlib import Path
from typing import override

from poetry.core.masonry.utils.helpers import distribution_name

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.files.models import PlatformDirectory, PlatformPackageFile
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.utils import platformdirs

logger = logging.getLogger(__name__)


class IncludeFilesHookBuilderError(Exception):
    pass


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
        self.__platform_directories = platformdirs.GenericPlatformDirectories(
            distribution_name(self.__poexy.package.name)
        )

    @override
    def build(self):
        with self._hook_build():
            logger.info("Resolving include files...")
            resolved = self.__poexy.resolve_inclusions(self.__format)
            resolved = resolved.filter_by_type(PlatformPackageFile)
            exclusions = [file.source for file in resolved.excludes]

            logger.info(f"Resolved {len(resolved.includes)} files to include.")
            logger.info(f"Resolved {len(resolved.excludes)} files to exclude.")

            count = 0

            for file in resolved.includes:
                if not isinstance(file, PlatformPackageFile):
                    raise IncludeFilesHookBuilderError(
                        f"File {file.source} is not a platform package file"
                    )
                if file.source in exclusions:
                    logger.info(f"Excluding file: {file.source}")
                    continue
                logger.info(f"Including file: {file.source}")
                if self.__format == PackageFormat.Wheel:
                    if file.target == PlatformDirectory.Config.value:
                        destination_path = self.__platform_directories.config
                    elif file.target == PlatformDirectory.Data.value:
                        destination_path = self.__platform_directories.data
                    elif file.target == PlatformDirectory.Cache.value:
                        destination_path = self.__platform_directories.cache
                    else:
                        raise IncludeFilesHookBuilderError(
                            f"Invalid platform directory: {file.target}"
                        )
                    destination_path = destination_path / file.destination
                elif self.__format == PackageFormat.Source:
                    destination_path = file.destination
                else:
                    raise IncludeFilesHookBuilderError(
                        f"Invalid package format: {self.__format}"
                    )
                self.__files.append(
                    (file.source, self.__destination / destination_path)
                )
                count += 1

            logger.info(f"{count} files ready to be packaged.")

    @override
    def add_files(self, callback: FilePathCallback):
        with self._hook_add_files():
            for source, destination in self.__files:
                callback(source, destination)
