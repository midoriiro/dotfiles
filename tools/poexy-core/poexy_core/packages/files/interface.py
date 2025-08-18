from abc import ABC
from typing import (
    TYPE_CHECKING,
    Iterable,
    Iterator,
    List,
    Optional,
    Self,
    Set,
    SupportsIndex,
    Type,
)

if TYPE_CHECKING:
    from .types import CollectionContainerType, PackageFileRewritter, PackageFileType

# pylint: disable=no-member,import-outside-toplevel


class FlexibleFiles(ABC):
    def __init__(
        self,
        _type: Type[Self],
        container_type: "CollectionContainerType",
        files: Iterable["PackageFileType"] = None,
    ):
        raise NotImplementedError("Subclass must implement this method")

    def filter_by_type(self, _type: Type["PackageFileType"]) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    @property
    def rewritter(self) -> Optional["PackageFileRewritter"]:
        raise NotImplementedError("Subclass must implement this method")

    @rewritter.setter
    def rewritter(self, rewritter: "PackageFileRewritter") -> None:
        raise NotImplementedError("Subclass must implement this method")

    def rewrite(self) -> None:
        raise NotImplementedError("Subclass must implement this method")

    def regulars(self) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    def symlinks(self) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    def platforms(self) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    def sources(self) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    def directories(self) -> Self:
        raise NotImplementedError("Subclass must implement this method")


class FrozenFiles(FlexibleFiles, ABC):
    def __init__(self, files: Set["PackageFileType"]):
        raise NotImplementedError("Subclass must implement this method")

    def unfreeze(self) -> "Files":
        raise NotImplementedError("Subclass must implement this method")


class Files(FlexibleFiles, ABC):
    def __init__(self, files: List["PackageFileType"]):
        raise NotImplementedError("Subclass must implement this method")

    def __reversed__(self) -> Iterator["PackageFileType"]:
        raise NotImplementedError("Subclass must implement this method")

    def get(self, index: SupportsIndex) -> "PackageFileType":
        raise NotImplementedError("Subclass must implement this method")

    def append(self, file: "PackageFileType") -> None:
        raise NotImplementedError("Subclass must implement this method")

    def extend(self, files: Iterable["PackageFileType"]) -> None:
        raise NotImplementedError("Subclass must implement this method")

    def update(self, file: "PackageFileType") -> None:
        raise NotImplementedError("Subclass must implement this method")

    def remove(self, file: "PackageFileType") -> None:
        raise NotImplementedError("Subclass must implement this method")

    def remove_by_type(self, _type: Type["PackageFileType"]):
        raise NotImplementedError("Subclass must implement this method")

    def reduce(self):
        raise NotImplementedError("Subclass must implement this method")

    def pop_by_type(self, _type: Type["PackageFileType"]) -> Self:
        raise NotImplementedError("Subclass must implement this method")

    def freeze(self) -> FrozenFiles:
        raise NotImplementedError("Subclass must implement this method")
