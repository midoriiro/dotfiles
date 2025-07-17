from pathlib import Path
from typing import override

from poetry.core.masonry.metadata import Metadata

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.builders.types import FilePathCallback
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy


class LicenseHookBuilder(HookBuilder):
    def __init__(self, poexy: Poexy, destination_path: Path):
        super().__init__("license")
        self.__poexy = poexy
        self.__destination_path = destination_path
        self.__files = []

    @override
    def build(self):
        with self._hook_build():
            if self.__poexy.license is None:
                return
            if self.__poexy.license.files is None:
                return
            if len(self.__poexy.license.files) == 0:
                return
            files = self.__poexy.license.resolve_files()
            if files is None:
                return
            for file in files:
                source = Path(file).resolve()
                destination = self.__destination_path / Path(file).name
                self.__files.append((source, destination))

    @override
    def add_files(self, callback: FilePathCallback):
        with self._hook_add_files():
            for source, destination in self.__files:
                callback(source, destination)

    @override
    def add_metadata(self, metadata: Metadata, _format: PackageFormat):
        with self._hook_add_metadata():
            if self.__poexy.license is None:
                return
            self.__poexy.license.transform_poetry_metadata(metadata, _format)
