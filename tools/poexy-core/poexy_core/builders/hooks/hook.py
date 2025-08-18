import logging
from contextlib import contextmanager
from typing import Generator

from poetry.core.masonry.metadata import Metadata

from poexy_core.builders.types import FilePathCallback, LinkPathCallback
from poexy_core.packages.format import PackageFormat

logger = logging.getLogger(__name__)


class HookBuilderError(Exception):
    pass


class HookBuilder:
    def __init__(self, name: str):
        self.__name = name

        self.__ensure_hook_name_is_set()
        self.__ensure_at_least_one_method_is_implemented()

    def __ensure_hook_name_is_set(self):
        if self.__name is None:
            raise HookBuilderError(
                "Hook name is not set. When subclassing HookBuilder, "
                "you must provide a name for the hook by call parent constructor."
            )

    def __ensure_at_least_one_method_is_implemented(self):
        is_add_files_implemented = self.add_files.__func__ is not HookBuilder.add_files
        is_add_links_implemented = self.add_links.__func__ is not HookBuilder.add_links
        is_add_metadata_implemented = (
            self.add_metadata.__func__ is not HookBuilder.add_metadata
        )

        if (
            is_add_files_implemented
            or is_add_links_implemented
            or is_add_metadata_implemented
        ):
            return

        methods = [
            self.add_files.__name__,
            self.add_links.__name__,
            self.add_metadata.__name__,
        ]
        methods = ", ".join(methods)

        raise HookBuilderError(
            f"Subclass must implement at least one method: {methods}"
        )

    @contextmanager
    def _hook_build(self) -> Generator[None, None, None]:
        self.__ensure_hook_name_is_set()
        logger.info(f"Building hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} built successfully.")

    def build(self):
        raise NotImplementedError("Subclass must implement build method")

    @contextmanager
    def _hook_add_files(self) -> Generator[None, None, None]:
        self.__ensure_hook_name_is_set()
        logger.info(f"Adding files from hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} added files successfully.")

    def add_files(self, callback: FilePathCallback):
        pass

    @contextmanager
    def _hook_add_links(self) -> Generator[None, None, None]:
        self.__ensure_hook_name_is_set()
        logger.info(f"Adding links from hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} added links successfully.")

    def add_links(self, callback: LinkPathCallback):
        pass

    @contextmanager
    def _hook_add_metadata(self) -> Generator[None, None, None]:
        self.__ensure_hook_name_is_set()
        logger.info(f"Adding metadata from hook: {self.__name}")
        yield
        logger.info(f"Hook {self.__name} added metadata successfully.")

    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        pass
