from pathlib import Path
from typing import override

from poetry.core.masonry.metadata import Metadata
from poetry.core.poetry import Poetry

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy


class ReadmeHookBuilder(HookBuilder):
    def __init__(self, poetry: Poetry, poexy: Poexy, destination_path: Path):
        super().__init__("readme")
        self.__poetry = poetry
        self.__poexy = poexy
        self.__destination_path = destination_path
        self.__files = []

    @override
    def build(self):
        with self._hook_build():
            if self.__poexy.readme is None:
                return
            self.__poexy.readme.transform_poetry_package(self.__poetry.package)
            self.__files.append(
                (
                    self.__poexy.readme.file.pattern,
                    self.__destination_path / self.__poexy.readme.file.pattern,
                )
            )

    @override
    def add_files(self, callback: FilePathCallback):
        if self.__poexy.readme is None:
            return
        for file in self.__files:
            callback(file[0], file[1])

    @override
    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        pass
