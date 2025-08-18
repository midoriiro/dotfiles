import logging
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Self, Set, Type, override

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from poexy_core.packages.files.collections import InclusionFiles
from poexy_core.packages.files.models import (
    DirectoryPackageFile,
    PackageFile,
    PlatformDirectory,
    PlatformPackageFile,
    ResolvedSymlinkPackageFile,
    SourcePackageFile,
    SymlinkPackageFile,
)
from poexy_core.packages.files.types import PackageFileRewritter
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.inclusions import Exclude, Excludes, Include, Includes
from poexy_core.packages.package import BasePackage
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.pyproject.types import GlobPattern
from poexy_core.utils.constants import SDIST_EXTENSIONS, WHEEL_EXTENSIONS

from .exceptions import (
    DirectoryResolvedNothingError,
    FormatNotAllowedError,
    NoFilesResolvedError,
    PatternResolvedNothingError,
    ResolverValidationError,
)
from .options import (
    DefaultRegularFileAccesser,
    DefaultRegularFileNormalizer,
    DefaultSymlinkAccesser,
    DefaultSymlinkNormalizer,
    DefaultSymlinkPolicy,
    ResolverAccesser,
    ResolverNormalizer,
    ResolverSymlinkPolicy,
)

if TYPE_CHECKING:
    from poexy_core.packages.files.collections import Files

# pylint: disable=no-member,import-outside-toplevel

logger = logging.getLogger(__name__)


class GlobPatternResolver(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    glob_pattern: Optional[Path] = Field(
        description="Glob pattern to match the files in the built archive"
    )
    path: Path = Field(description="Path where to match the files")
    recursive: bool = Field(default=True)
    accesser: Optional[ResolverAccesser] = None
    normalizer: Optional[ResolverNormalizer] = None
    symlink_accesser: Optional[ResolverAccesser] = None
    symlink_normalizer: Optional[ResolverNormalizer] = None
    symlink_policy: Optional[ResolverSymlinkPolicy] = None
    __implementation: Self

    @override
    def model_post_init(self, __context: Any, /) -> None:
        if self.accesser is None:
            self.accesser = DefaultRegularFileAccesser()
        if self.normalizer is None:
            self.normalizer = DefaultRegularFileNormalizer(self.accesser)
        if self.symlink_policy is None:
            self.symlink_policy = DefaultSymlinkPolicy()
        if self.symlink_accesser is None:
            self.symlink_accesser = DefaultSymlinkAccesser(self.symlink_policy)
        if self.symlink_normalizer is None:
            self.symlink_normalizer = DefaultSymlinkNormalizer(
                self.accesser, self.symlink_policy
            )

        if self.__class__.__name__ != GlobPatternResolver.__name__:
            return

        from .implementation import DefaultGlobPatternResolver

        self.__implementation = DefaultGlobPatternResolver(
            **self.model_dump(exclude={"__implementation"})
        )

    @model_validator(mode="after")
    def validate_model(self) -> "GlobPatternResolver":
        if self.glob_pattern is not None and self.glob_pattern.is_absolute():
            raise ValueError("Glob pattern must be relative")
        if self.glob_pattern is not None and "*" not in str(self.glob_pattern):
            raise ValueError("Invalid glob pattern")
        return self

    def resolve(self) -> "Files":
        return self.__implementation.resolve()


class FileResolver(ABC, BaseModel):
    format: PackageFormat = Field(description="Format of the files to resolve")
    _all_patterns_should_resolve: bool = PrivateAttr(default=True)
    _patterns: List[GlobPattern] = PrivateAttr(default_factory=list)
    _resolvers: List[GlobPatternResolver] = PrivateAttr(default_factory=list)
    _extensions: Set[str] = PrivateAttr(default_factory=list)

    @override
    def model_post_init(self, __context: Any, /) -> None:
        if self.format == PackageFormat.Source:
            self._extensions = SDIST_EXTENSIONS
        elif self.format == PackageFormat.Wheel:
            self._extensions = WHEEL_EXTENSIONS
        else:
            raise ValueError(f"Unsupported format: {self.format}")

        self._extensions = set(self._extensions)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if len(self._patterns) == 0:
            raise ResolverValidationError(
                self.__class__.__name__,
                "No patterns provided",
            )

        for pattern in self._patterns:
            path, glob_pattern = pattern.split()
            self._resolvers.append(
                GlobPatternResolver(glob_pattern=glob_pattern, path=path)
            )

    def __resolve_directories(self, files: "Files"):
        directories: List[DirectoryPackageFile] = list(files.directories())

        if len(directories) == 0:
            return

        files.remove_by_type(DirectoryPackageFile)

        directories_that_resolved_nothing: List[DirectoryPackageFile] = []

        for directory in directories:
            try:
                directory_resolved_files = directory.resolve()
                files.extend(directory_resolved_files)
            except DirectoryResolvedNothingError as exc:
                if self._all_patterns_should_resolve:
                    raise exc
                directories_that_resolved_nothing.append(directory)
                continue

        if len(directories_that_resolved_nothing) > 0:
            directories = ", ".join(
                [
                    str(directory.source)
                    for directory in directories_that_resolved_nothing
                ]
            )
            raise DirectoryResolvedNothingError(directory=directories)

        files.reduce()

        return

    def resolve(self) -> "Files":
        from poexy_core.packages.files.collections import Files

        resolved = Files(list())

        revolvers_that_resolved_nothing: List[GlobPatternResolver] = []

        for resolver in self._resolvers:
            try:
                resolved.extend(resolver.resolve())
            except NoFilesResolvedError as exc:
                if self._all_patterns_should_resolve:
                    raise exc
                revolvers_that_resolved_nothing.append(resolver)
                continue

        if len(resolved) == 0:
            patterns = ", ".join(
                [
                    str(resolver.glob_pattern)
                    for resolver in revolvers_that_resolved_nothing
                ]
            )
            raise PatternResolvedNothingError(pattern=patterns)

        resolved.reduce()

        self.__resolve_directories(resolved)

        return resolved


class SourceFileResolver(FileResolver):
    path: Path = Field(description="Path to match the files")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        for extension in self._extensions:
            pattern = self.path / f"**/*{extension}"
            self._patterns.append(GlobPattern(pattern=pattern))

        self._all_patterns_should_resolve = False
        super().validate_model()
        return self

    @override
    def resolve(self) -> "Files":
        from poexy_core.packages.files.collections import Files

        resolved = super().resolve()

        resolved.remove_by_type(SymlinkPackageFile)

        resolved = list(
            map(
                lambda file: SourcePackageFile(
                    source=file.source,
                    destination=file.destination,
                ),
                resolved,
            )
        )

        return Files(resolved)


class SymlinkFileResolver(FileResolver):
    path: Path = Field(description="Path to match the files")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        pattern = self.path / "**/*"
        self._patterns.append(GlobPattern(pattern=pattern))
        super().validate_model()
        return self

    @override
    def resolve(self) -> "Files":
        resolved = super().resolve()
        return resolved.symlinks()


class GlobPatternFileResolver(FileResolver, ABC):
    project_path: Path = Field(description="Path to the project")
    source_path: Path = Field(description="Path to the source package")
    _pattern: Optional[GlobPattern] = PrivateAttr(default=None)
    _platform_directory: Optional[PlatformDirectory] = PrivateAttr(
        default=None,
    )

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        if self._pattern is None:
            raise ResolverValidationError(
                self.__class__.__name__,
                "Pattern is required",
            )

        self._patterns.append(self._pattern)
        self.project_path = self.project_path.absolute()
        self.source_path = self.source_path.absolute()
        super().validate_model()
        return self

    def __map_package_file(self, file: PackageFile) -> PackageFile:
        if isinstance(file, SymlinkPackageFile):
            return file

        if file.source.resolve().is_relative_to(self.source_path):
            return SourcePackageFile(source=file.source, destination=file.destination)

        if self.format == PackageFormat.Source:
            return SourcePackageFile(source=file.source, destination=file.destination)

        if self._platform_directory is not None:
            return PlatformPackageFile(
                source=file.source,
                destination=file.destination,
                target=self._platform_directory,
            )

        logger.warning(
            f"File '{file.source}' detected as platform package file "
            "but no platform directory destination is specified in the "
            "include configuration. Using data directory as default "
            "target. If you want to use a different platform "
            "directory, please specify the destination field in "
            "include configuration."
        )

        return PlatformPackageFile(
            source=file.source,
            destination=file.destination,
            target=PlatformDirectory.Data,
        )

    def __map_package_files(self, files: "Files"):
        for file in files:
            files.update(self.__map_package_file(file))

    def __resolve_symlink_target_directory(self, files: "Files"):
        from poexy_core.packages.files.collections import Files

        resolved_symlink_files = Files(list())
        indexes_to_remove: List[int] = list()

        for index, file in enumerate(files):
            if not isinstance(file, SymlinkPackageFile):
                continue

            if not file.target.is_dir():
                continue

            resolved_symlink_files.extend(file.resolve())
            indexes_to_remove.append(index)

        if len(indexes_to_remove) == 0:
            return

        self.__resolve_symlink_target_file(
            resolved_symlink_files, ResolvedSymlinkPackageFile
        )

        if self.format == PackageFormat.Source:
            resolved_symlink_files.remove_by_type(ResolvedSymlinkPackageFile)
            resolved_symlink_files.reduce()
            files.extend(resolved_symlink_files)
            return

        files_to_remove = [files.get(index) for index in indexes_to_remove]

        for file in reversed(files_to_remove):
            files.remove(file)

        resolved_symlink_files.reduce()

        files.extend(resolved_symlink_files)

    def __resolve_symlink_target_file(
        self,
        files: "Files",
        _type: Type[SymlinkPackageFile],
    ):
        resolved_symlink_files: List[PackageFile] = list()

        for file in files:
            if not isinstance(file, _type):
                continue

            source = file.source.resolve().relative_to(self.project_path)
            destination = source

            if source.is_dir():
                continue

            if source.suffix in self._extensions:
                continue

            resolved_symlink_files.append(
                SourcePackageFile(
                    source=source,
                    destination=destination,
                )
            )

        if len(resolved_symlink_files) == 0:
            return

        files.extend(resolved_symlink_files)

    @override
    def resolve(self) -> "Files":
        resolved = super().resolve()
        self.__resolve_symlink_target_directory(resolved)
        self.__resolve_symlink_target_file(resolved, SymlinkPackageFile)
        self.__map_package_files(resolved)
        return resolved


class IncludeFileResolver(GlobPatternFileResolver):
    include: Include = Field(description="Include to resolve")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        if self.format not in self.include.formats:
            raise FormatNotAllowedError(self.__class__.__name__, self.format)

        if self.include.destination is not None and self.format == PackageFormat.Source:
            raise ResolverValidationError(
                self.__class__.__name__,
                "Destination property in include configuration is only allowed with "
                "wheel format",
            )

        if self.include.destination is not None:
            self._platform_directory = self.include.destination

        self._pattern = self.include.path
        super().validate_model()
        return self

    @override
    def resolve(self) -> "Files":
        try:
            return super().resolve()
        except PatternResolvedNothingError as exc:
            from poexy_core.packages.files.collections import Files

            logger.warning(f"Pattern '{exc.pattern}' resolved nothing")

            return Files(list())


class ExcludeFileResolver(GlobPatternFileResolver):
    exclude: Exclude = Field(description="Exclude to resolve")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        if self.exclude.formats is not None and self.format not in self.exclude.formats:
            raise FormatNotAllowedError(self.__class__.__name__, self.format)

        self._pattern = self.exclude.path
        super().validate_model()
        return self

    @override
    def resolve(self) -> "Files":
        try:
            return super().resolve()
        except PatternResolvedNothingError as exc:
            from poexy_core.packages.files.collections import Files

            logger.warning(f"Pattern '{exc.pattern}' resolved nothing")

            return Files(list())


class PackageFileResolver(ABC, BaseModel):
    format: PackageFormat = Field(description="Format of the files to resolve")
    project_path: Path = Field(description="Path to the project")
    source_path: Path = Field(description="Path to the source package")
    _resolvers: List[FileResolver] = PrivateAttr(default_factory=list)
    _extensions: Set[str] = PrivateAttr(default_factory=list)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if len(self._resolvers) == 0:
            raise ResolverValidationError(
                self.__class__.__name__,
                "No resolvers provided",
            )

        if self.format == PackageFormat.Source:
            self._extensions = SDIST_EXTENSIONS
        elif self.format == PackageFormat.Wheel:
            self._extensions = WHEEL_EXTENSIONS
        else:
            raise ValueError(f"Unsupported format: {self.format}")

        self._extensions = set(self._extensions)

        self.project_path = self.project_path.absolute()
        self.source_path = self.source_path.absolute()

    def post_resolve(self, resolved: "Files"):
        pass

    def resolve(self) -> "Files":
        from poexy_core.packages.files.collections import Files

        resolved = Files(list())

        for resolver in self._resolvers:
            resolved_files = resolver.resolve()
            self.post_resolve(resolved_files)
            resolved.extend(resolved_files)

        return resolved


class ModuleFileResolver(PackageFileResolver):
    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        self._resolvers.append(
            SourceFileResolver(format=self.format, path=self.source_path)
        )
        self._resolvers.append(
            SymlinkFileResolver(format=self.format, path=self.source_path)
        )
        super().validate_model()
        return self

    @override
    def post_resolve(self, resolved: "Files"):
        symlinks: List[SymlinkPackageFile] = list(resolved.symlinks())

        for symlink in symlinks:
            suffix = symlink.target.suffix

            if suffix not in self._extensions:
                resolved.remove(symlink)


class IncludesFileResolver(PackageFileResolver):
    includes: Includes = Field(min_length=1, description="Includes to resolve")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        for include in self.includes:
            self._resolvers.append(
                IncludeFileResolver(
                    format=self.format,
                    project_path=self.project_path,
                    source_path=self.source_path,
                    include=include,
                )
            )
        super().validate_model()
        return self


class ExcludesFileResolver(PackageFileResolver):
    excludes: Excludes = Field(min_length=1, description="Excludes to resolve")

    @model_validator(mode="after")
    @override
    def validate_model(self) -> Self:
        for exclude in self.excludes:
            self._resolvers.append(
                ExcludeFileResolver(
                    format=self.format,
                    project_path=self.project_path,
                    source_path=self.source_path,
                    exclude=exclude,
                )
            )
        super().validate_model()
        return self


class PackageResolver(BaseModel):
    format: PackageFormat = Field(description="Format of the files to resolve")
    project_path: Path = Field(description="Path to the project")
    source_path: Path = Field(description="Path to the source package")
    poexy: Poexy = Field(description="Package to resolve")
    _resolved_module_files: Optional["Files"] = PrivateAttr(default=None)
    _resolved_inclusions_files: Optional[InclusionFiles] = PrivateAttr(default=None)

    def __rewrite_file_destination(self, file: PackageFile):
        package_source = self.poexy.package.source
        package_name = self.poexy.package.name
        if file.source.is_relative_to(package_source):
            parts = list(file.destination.parts)
            for index, part in enumerate(parts):
                if part == package_source.name:
                    parts.pop(index)
                    file.destination = Path(package_name) / Path(*parts)
                    break

    def __package_file_rewritter(self) -> PackageFileRewritter:
        def rewritter(file: PackageFile):
            self.__rewrite_file_destination(file)

        return rewritter

    def __resolve_inclusion_files(
        self,
        package: Optional[BasePackage],
        includes: "Files",
        excludes: "Files",
    ) -> InclusionFiles:
        if package is None:
            return

        if package.includes is not None:
            try:
                resolver = IncludesFileResolver(
                    format=self.format,
                    project_path=self.project_path,
                    source_path=self.source_path,
                    includes=package.includes,
                )
            except FormatNotAllowedError:
                return
            resolved_files = resolver.resolve()
            includes.extend(resolved_files)

        if package.excludes is not None:
            try:
                resolver = ExcludesFileResolver(
                    format=self.format,
                    project_path=self.project_path,
                    source_path=self.source_path,
                    excludes=package.excludes,
                )
            except FormatNotAllowedError:
                return
            resolved_files = resolver.resolve()
            excludes.extend(resolved_files)

    def resolve_module_files(self) -> "Files":
        if self._resolved_module_files is not None:
            return self._resolved_module_files

        resolver = ModuleFileResolver(
            format=self.format,
            project_path=self.project_path,
            source_path=self.source_path,
        )

        resolved_files = resolver.resolve()
        resolved_files.rewritter = self.__package_file_rewritter()

        resolved_inclusions = self.resolve_inclusions()
        resolved_inclusions = resolved_inclusions.filter_by_type(SourcePackageFile)
        resolved_inclusions.apply_includes(resolved_files)
        resolved_inclusions.apply_excludes(resolved_files)

        if (
            self.format == PackageFormat.Wheel
            and self.poexy.package.source.name != self.poexy.package.name
        ):
            resolved_files.rewrite()

        self._resolved_module_files = resolved_files.freeze()

        return self._resolved_module_files

    def resolve_inclusions(self) -> InclusionFiles:
        if self._resolved_inclusions_files is not None:
            return self._resolved_inclusions_files

        from poexy_core.packages.files.collections import Files

        includes: Files = Files(list())
        excludes: Files = Files(list())

        self.__resolve_inclusion_files(self.poexy.package, includes, excludes)
        self.__resolve_inclusion_files(self.poexy.wheel, includes, excludes)
        self.__resolve_inclusion_files(self.poexy.sdist, includes, excludes)
        self.__resolve_inclusion_files(self.poexy.binary, includes, excludes)

        includes.rewritter = self.__package_file_rewritter()
        excludes.rewritter = self.__package_file_rewritter()

        if (
            self.format == PackageFormat.Wheel
            and self.poexy.package.source.name != self.poexy.package.name
        ):
            includes.rewrite()
            excludes.rewrite()

        self._resolved_inclusions_files = InclusionFiles(
            includes=includes.freeze(), excludes=excludes.freeze()
        )

        return self._resolved_inclusions_files
