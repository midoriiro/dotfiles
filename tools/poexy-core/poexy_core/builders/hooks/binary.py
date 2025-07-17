from typing import override

from poetry.core.masonry.metadata import Metadata

from poexy_core.builders.binary import BinaryBuilder
from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.format import PackageFormat


class BinaryHookBuilder(HookBuilder):
    def __init__(self, builder: BinaryBuilder):
        super().__init__("binary")
        self.__builder = builder
        self.__destination = builder._metadata.data_scripts_folder
        self.__files = []

    @override
    def build(self):
        with self._hook_build():
            source, destination = self.__builder.build_executable()
            self.__files.append((source, destination))

    @override
    def add_files(self, callback: FilePathCallback):
        with self._hook_add_files():
            for source, destination in self.__files:
                callback(source, self.__destination / destination)

    @override
    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        pass
