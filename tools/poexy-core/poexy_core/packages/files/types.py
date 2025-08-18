from enum import Enum
from typing import Callable, Union

from .models import (
    DirectoryPackageFile,
    PackageFile,
    PlatformPackageFile,
    SourcePackageFile,
    SymlinkPackageFile,
)

PackageFileType = Union[
    PackageFile,
    SymlinkPackageFile,
    PlatformPackageFile,
    SourcePackageFile,
    DirectoryPackageFile,
]

PackageFileRewritter = Callable[[PackageFile], None]


class CollectionContainerType(str, Enum):
    List = "list"
    Set = "set"
