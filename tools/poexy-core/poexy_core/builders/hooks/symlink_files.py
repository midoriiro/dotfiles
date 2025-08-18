import logging
from typing import override

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathPredicate, LinkPathCallback
from poexy_core.packages.files.models import (
    ResolvedSymlinkPackageFile,
    SymlinkPackageFile,
)
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy

logger = logging.getLogger(__name__)


class SymlinkFilesHookBuilderError(Exception):
    pass


class SymlinkFilesHookBuilder(HookBuilder):

    def __init__(
        self,
        poexy: Poexy,
        _format: PackageFormat,
        destination_predicate: FilePathPredicate,
    ):
        super().__init__("symlink_files")
        self.__poexy = poexy
        self.__format = _format
        self.__destination_predicate = destination_predicate
        self.__links = []

    @override
    def build(self):
        with self._hook_build():
            logger.info("Resolving symlink files...")
            resolved = self.__poexy.resolve_module_files(self.__format)
            resolved = resolved.filter_by_type(SymlinkPackageFile).unfreeze()
            inclusions = self.__poexy.resolve_inclusions(self.__format)
            inclusions = inclusions.filter_by_type(SymlinkPackageFile)
            inclusions.apply_includes(resolved)
            inclusions.apply_excludes(resolved)
            excludes = [path.source for path in inclusions.excludes]

            resolved = resolved.freeze()

            logger.info(f"Resolved {len(resolved)} symlink files.")
            logger.info(f"Resolved {len(inclusions.includes)} files to include.")
            logger.info(f"Resolved {len(inclusions.excludes)} files to exclude.")

            count = 0

            for file in resolved:
                if not isinstance(file, SymlinkPackageFile):
                    raise SymlinkFilesHookBuilderError(
                        f"File {file.source} is not a symlink package file"
                    )

                if file.source in excludes:
                    logger.info(f"Excluding file: {file.source}")
                    continue

                if isinstance(file, ResolvedSymlinkPackageFile):
                    destination = self.__destination_predicate(file.source)
                    target = file.symlink.target
                else:
                    destination = self.__destination_predicate(file.target)
                    target = file.target

                if destination is None:
                    logger.info(f"Excluding file: {file.source}")
                    continue

                logger.info(f"Including file: {file.source}")
                self.__links.append(
                    (file.source, destination / file.destination, target)
                )
                count += 1

            logger.info(f"{count} files ready to be packaged.")

    @override
    def add_links(self, callback: LinkPathCallback):
        sorted_links = sorted(self.__links, key=lambda x: x[0])
        with self._hook_add_links():
            for source, destination, target in sorted_links:
                callback(source, destination, target)
