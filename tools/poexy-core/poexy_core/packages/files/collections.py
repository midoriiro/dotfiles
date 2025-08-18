from pathlib import Path
from typing import (
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Self,
    Set,
    SupportsIndex,
    Type,
)

from pydantic import BaseModel, ConfigDict, Field

from .interface import Files as FilesInterface
from .interface import FlexibleFiles as FlexibleFilesInterface
from .interface import FrozenFiles as FrozenFilesInterface
from .types import CollectionContainerType, PackageFileRewritter, PackageFileType

# pylint: disable=no-member,import-outside-toplevel


class FilesMixin:
    def _regulars(self, files: Iterable[PackageFileType]) -> Set[PackageFileType]:
        from .models import PackageFile

        return [file for file in files if not isinstance(file, PackageFile)]

    def _symlinks(self, files: Iterable[PackageFileType]) -> Set[PackageFileType]:
        from .models import SymlinkPackageFile

        return [file for file in files if isinstance(file, SymlinkPackageFile)]

    def _platforms(self, files: Iterable[PackageFileType]) -> Set[PackageFileType]:
        from .models import PlatformPackageFile

        return [file for file in files if isinstance(file, PlatformPackageFile)]

    def _sources(self, files: Iterable[PackageFileType]) -> Set[PackageFileType]:
        from .models import SourcePackageFile

        return [file for file in files if isinstance(file, SourcePackageFile)]

    def _directories(self, files: Iterable[PackageFileType]) -> Set[PackageFileType]:
        from .models import DirectoryPackageFile

        return [file for file in files if isinstance(file, DirectoryPackageFile)]


class FlexibleFiles(FlexibleFilesInterface, FilesMixin):
    def __init__(
        self,
        _type: Type[Self],
        container_type: CollectionContainerType,
        files: Iterable[PackageFileType] = None,
    ):
        self.__type = _type
        self.__rewritter: Optional[PackageFileRewritter] = None

        if container_type == CollectionContainerType.Set:
            self._container: Set[PackageFileType] = set()
        elif container_type == CollectionContainerType.List:
            self._container: List[PackageFileType] = list()

        if isinstance(files, list) and isinstance(self._container, list):
            self._container.extend(files)
        elif isinstance(files, set) and isinstance(self._container, list):
            self._container.extend(list(files))
        elif isinstance(files, set) and isinstance(self._container, set):
            self._container.update(files)
        elif isinstance(files, list) and isinstance(self._container, set):
            self._container.update(set(files))
        else:
            raise ValueError(f"Invalid files type: {type(files)}")

    def _transfert(self, other: Self) -> None:
        other.rewritter = self.__rewritter

    def _copy(self, files: Iterable[PackageFileType]) -> Self:
        return self._copy_as(files, self.__type)

    def _copy_as(self, files: Iterable[PackageFileType], _type: Type[Self]) -> Self:
        files = _type(files)
        self._transfert(files)
        return files

    def __iter__(self) -> Iterator[PackageFileType]:
        return iter(self._container)

    def __len__(self) -> int:
        return len(self._container)

    def __contains__(self, item: PackageFileType) -> bool:
        return item in self._container

    def filter_by_type(self, _type: Type[PackageFileType]) -> Self:
        if isinstance(self._container, list):
            container = list
        elif isinstance(self._container, set):
            container = set
        else:
            raise ValueError(f"Invalid container type: {type(self._container)}")

        files = filter(lambda file: isinstance(file, _type), self._container)
        files = container(files)
        files = self._copy(files)
        return files

    @property
    def rewritter(self) -> Optional[PackageFileRewritter]:
        return self.__rewritter

    @rewritter.setter
    def rewritter(self, rewritter: PackageFileRewritter) -> None:
        self.__rewritter = rewritter

    def rewrite(self) -> None:
        if self.__rewritter is None:
            return
        for file in self._container:
            self.__rewritter(file)

    def regulars(self) -> Self:
        files = self._regulars(self._container)
        files: Self = self._copy(files)
        return files

    def symlinks(self) -> Self:
        files = self._symlinks(self._container)
        files: Self = self._copy(files)
        return files

    def platforms(self) -> Self:
        files = self._platforms(self._container)
        files: Self = self._copy(files)
        return files

    def sources(self) -> Self:
        files = self._sources(self._container)
        files: Self = self._copy(files)
        return files

    def directories(self) -> Self:
        files = self._directories(self._container)
        files: Self = self._copy(files)
        return files


class FrozenFiles(FrozenFilesInterface, FlexibleFiles):
    def __init__(self, files: Set[PackageFileType]):
        FlexibleFiles.__init__(
            self,
            FrozenFiles,
            CollectionContainerType.Set,
            files,
        )

    def unfreeze(self) -> "Files":
        files = self._copy_as(self._container, Files)
        return files


class Files(FilesInterface, FlexibleFiles):
    def __init__(self, files: List[PackageFileType]):
        FlexibleFiles.__init__(
            self,
            Files,
            CollectionContainerType.List,
            files,
        )

    def __reversed__(self) -> Iterator[PackageFileType]:
        return reversed(self._container)

    def get(self, index: SupportsIndex) -> PackageFileType:
        return self._container[index]

    def append(self, file: PackageFileType) -> None:
        self._container.append(file)

    def extend(self, files: Iterable[PackageFileType]) -> None:
        self._container.extend(files)

    def update(self, file: PackageFileType) -> None:
        index = self._container.index(file)
        self._container[index] = file

    def remove(self, file: PackageFileType) -> None:
        self._container.remove(file)

    def remove_by_type(self, _type: Type[PackageFileType]):
        indexes_to_remove: List[int] = []

        for index, file in enumerate(self._container):
            if isinstance(file, _type):
                indexes_to_remove.append(index)

        if len(indexes_to_remove) == 0:
            return

        for index in reversed(indexes_to_remove):
            del self._container[index]

    def pop_by_type(self, _type: Type[PackageFileType]) -> Self:
        files: List[PackageFileType] = []
        indexes_to_remove: List[int] = []

        for index, file in enumerate(self._container):
            if isinstance(file, _type):
                files.append(file)
                indexes_to_remove.append(index)

        if len(files) == 0:
            return self

        for index in reversed(indexes_to_remove):
            del self._container[index]

        files = self._copy(files)

        return files

    def reduce(self):
        hash_map: Dict[int, PackageFileType] = {}

        indexes_to_remove: List[int] = []

        for index, file in enumerate(self._container):
            file_hash = hash(file)

            if file_hash in hash_map:
                indexes_to_remove.append(index)
            else:
                hash_map[file_hash] = file

        if len(indexes_to_remove) == 0:
            return

        for index in reversed(indexes_to_remove):
            del self._container[index]

    def freeze(self) -> FrozenFiles:
        from .models import SymlinkPackageFile

        best: Dict[Path, PackageFileType] = {}
        for file in self._container:
            current = best.get(file.destination, None)
            if current is None or (
                isinstance(file, SymlinkPackageFile)
                and not isinstance(current, SymlinkPackageFile)
            ):
                best[file.destination] = file
        files = self._copy_as(set(best.values()), FrozenFiles)
        return files


class InclusionFiles(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    includes: FrozenFiles = Field(description="Includes files")
    excludes: FrozenFiles = Field(description="Excludes files")

    def apply_includes(self, files: Files):
        if len(self.includes) == 0:
            return files
        for file in self.includes:
            if file not in files:
                files.append(file)

    def apply_excludes(self, files: Files):
        if len(self.excludes) == 0:
            return files
        for exclude_file in self.excludes:
            for file in files:
                if file.source == exclude_file.source:
                    files.remove(file)

    def filter_by_type(self, _type: Type[PackageFileType]) -> Self:
        includes = set(self.includes.filter_by_type(_type))
        excludes = set(self.excludes.filter_by_type(_type))
        return InclusionFiles(
            includes=FrozenFiles(includes),
            excludes=FrozenFiles(excludes),
        )
