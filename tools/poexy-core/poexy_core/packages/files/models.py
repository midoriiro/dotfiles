from collections import deque
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Optional, override

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .interface import Files
    from .resolvers.options import PackageFileResolverOptions

# pylint: disable=no-member,import-outside-toplevel


class PlatformDirectory(str, Enum):
    Config = "config"
    Data = "data"
    Cache = "cache"


class PackageFile(BaseModel):
    source: Path = Field(description="Source path where file will be copied from")
    destination: Path = Field(
        description="Destination path where file will be copied to"
    )

    def __eq__(self, other: "PackageFile") -> bool:
        return self.source == other.source

    def __ne__(self, value: "PackageFile") -> bool:
        return not self == value

    def __lt__(self, other: "PackageFile") -> bool:
        if self.destination.parent != other.destination.parent:
            return str(self.destination.parent) < str(other.destination.parent)
        return self.destination.name < other.destination.name

    def __le__(self, other: "PackageFile") -> bool:
        return self < other or self == other

    def __gt__(self, other: "PackageFile") -> bool:
        return not self <= other

    def __ge__(self, other: "PackageFile") -> bool:
        return not self < other

    def __hash__(self) -> int:
        return hash(self.source)


class SymlinkPackageFile(PackageFile):
    target: Path = Field(description="Target path of the symlink")

    def resolve(self) -> Optional["Files"]:
        from .collections import Files
        from .resolvers.exceptions import (
            NoFilesResolvedError,
            SymlinkResolvedNothingError,
        )
        from .resolvers.options import PackageFileResolverOptions

        if not self.target.is_dir():
            return None

        result = Files(list())
        directory = DirectoryPackageFile(source=self.source)
        queue = deque([directory])

        resolver_options = PackageFileResolverOptions(
            recursive=False,
        )

        while queue:
            current_directory = queue.popleft()
            try:
                resolved_files = current_directory.resolve(resolver_options)
                for file in resolved_files:
                    if isinstance(file, SymlinkPackageFile):
                        if file.target.is_dir():
                            directory = DirectoryPackageFile(
                                source=file.target,
                                destination=self.source / file.destination.name,
                            )
                            queue.append(directory)
                        else:
                            result.append(file)
                    elif isinstance(file, DirectoryPackageFile):
                        queue.append(file)
                    elif isinstance(file, PackageFile):
                        if not file.destination.is_relative_to(self.source):
                            file.destination = self.source / file.destination.name
                            if not file.destination.exists():
                                continue
                        result.append(
                            ResolvedSymlinkPackageFile(
                                source=file.source,
                                destination=file.destination,
                                symlink=self,
                            )
                        )
            except NoFilesResolvedError:
                continue

        if len(result) == 0:
            raise SymlinkResolvedNothingError(symlink=self.source)

        return result


class ResolvedSymlinkPackageFile(SymlinkPackageFile):
    target: ClassVar[Optional[Path]] = Field(default=None, exclude=True)

    symlink: SymlinkPackageFile = Field(
        description="Original symlink file from which this resolved file was derived"
    )

    @override
    def model_post_init(self, __context: Any, /) -> None:
        ResolvedSymlinkPackageFile.target = None

    @override
    def __hash__(self) -> int:
        return hash(self.destination)


class PlatformPackageFile(PackageFile):
    target: PlatformDirectory = Field(description="Target platform directory")


class SourcePackageFile(PackageFile):
    pass


class DirectoryPackageFile(PackageFile):
    destination: Optional[Path] = Field(default=None)

    def resolve(
        self, options: Optional["PackageFileResolverOptions"] = None
    ) -> "Files":
        from .collections import Files
        from .resolvers.exceptions import (
            DirectoryResolvedNothingError,
            PatternResolvedNothingError,
        )
        from .resolvers.models import GlobPatternResolver
        from .resolvers.options import PackageFileResolverOptions

        if options is None:
            options = PackageFileResolverOptions()

        result = Files(list())
        queue = deque(
            [
                GlobPatternResolver(
                    glob_pattern=Path("*"), path=self.source, **options.get()
                )
            ]
        )

        while queue:
            current_resolver = queue.popleft()
            try:
                resolved_files = current_resolver.resolve()
                directory_files = resolved_files.pop_by_type(DirectoryPackageFile)
                result.extend(resolved_files)
                for file in directory_files:
                    queue.append(
                        GlobPatternResolver(
                            glob_pattern=Path("*"),
                            path=file.source,
                            **options.get(),
                        )
                    )
            except PatternResolvedNothingError:
                continue

        if len(result) == 0:
            raise DirectoryResolvedNothingError(directory=self.source)

        return result
