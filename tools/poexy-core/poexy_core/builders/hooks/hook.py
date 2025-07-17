import logging
from contextlib import contextmanager
from typing import Generator

from poetry.core.masonry.metadata import Metadata

from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.format import PackageFormat

logger = logging.getLogger(__name__)


class HookBuilder:
    def __init__(self, name: str):
        self.__name = name

    @contextmanager
    def _hook_build(self) -> Generator[None, None, None]:
        logger.info(f"Building hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} built successfully.")

    def build(self):
        raise NotImplementedError("Subclass must implement build method")

    @contextmanager
    def _hook_add_files(self) -> Generator[None, None, None]:
        logger.info(f"Adding files from hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} added files successfully.")

    def add_files(self, callback: FilePathCallback):
        raise NotImplementedError("Subclass must implement add_files method")

    @contextmanager
    def _hook_add_metadata(self) -> Generator[None, None, None]:
        logger.info(f"Adding metadata from hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} added metadata successfully.")

    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        raise NotImplementedError("Subclass must implement add_metadata method")
