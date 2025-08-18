import logging
from typing import override

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback, FilePathPredicate
from poexy_core.packages.files.models import SourcePackageFile
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class PackageFilesHookBuilderError(Exception):
    pass


class PackageFilesHookBuilder(HookBuilder):
    def __init__(
        self,
        poexy: Poexy,
        _format: PackageFormat,
        destination_predicate: FilePathPredicate,
    ):
        super().__init__("package_files")
        self.__poexy = poexy
        self.__format = _format
        self.__destination_predicate = destination_predicate
        self.__files = []

    @override
    def build(self):
        with self._hook_build():
            logger.info("Resolving package files...")
            resolved = self.__poexy.resolve_module_files(self.__format)
            resolved = resolved.filter_by_type(SourcePackageFile)
            inclusions = self.__poexy.resolve_inclusions(self.__format)
            excludes = [path.source for path in inclusions.excludes]

            logger.info(f"Resolved {len(resolved)} package files.")

            count = 0

            for file in resolved:
                if not isinstance(file, SourcePackageFile):
                    raise PackageFilesHookBuilderError(
                        f"File {file.source} is not a source package file"
                    )

                if file.source in excludes:
                    logger.info(f"Excluding file: {file.source}")
                    continue

                destination = self.__destination_predicate(file.source)

                if destination is None:
                    logger.info(f"Excluding file: {file.source}")
                    continue

                logger.info(f"Including file: {file.source}")

                self.__files.append((file.source, destination / file.destination))

                count += 1

            logger.info(f"{count} files ready to be packaged.")

    @override
    def add_files(self, callback: FilePathCallback):
        with self._hook_add_files():
            for source, destination in self.__files:
                callback(source, destination)
