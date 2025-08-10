from pathlib import Path
from typing import Optional, Set

from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.format import PackageFormat
from poexy_core.utils.symbolic_link import SymbolicLink

# pylint: disable=no-member

SDIST_EXTENSIONS = {".py", ".c", ".cpp", ".h"}

WHEEL_EXTENSIONS = {
    ".py",
    ".pyd",
    ".so",
    ".dll",
    ".dylib",
}

GLOB_EXTENSIONS = {
    *SDIST_EXTENSIONS,
    *WHEEL_EXTENSIONS,
}

FORBIDDEN_DIRS = {
    "__pycache__",
    "build",
    "dist",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
}


class PackageFile(BaseModel):
    source: Path = Field(description="Source path where file will be copied from")
    destination: Path = Field(
        description="Destination path where file will be copied to"
    )

    def __eq__(self, other: "PackageFile") -> bool:
        return self.source == other.source and self.destination == other.destination

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
        return hash((self.source, self.destination))


PackageFiles = Set[PackageFile]


class ResolvedPackageFiles(BaseModel):
    includes: PackageFiles = Field(description="Includes files")
    excludes: PackageFiles = Field(description="Excludes files")

    @model_validator(mode="after")
    def validate_model(self) -> "ResolvedPackageFiles":
        self.includes = set(sorted(self.includes))
        self.excludes = set(self.excludes)
        return self

    def apply_includes(self, files: PackageFiles) -> PackageFiles:
        if len(self.includes) == 0:
            return files
        files = list(files)
        for file in self.includes:
            if file not in files:
                files.append(file)
        return set(files)

    def apply_excludes(self, files: PackageFiles) -> PackageFiles:
        if len(self.excludes) == 0:
            return files
        files = list(files)
        for exclude_file in self.excludes:
            for file in files:
                if file.source == exclude_file.source:
                    files.remove(file)
        return set(files)


class ResolvePackageFiles:
    def resolve(
        self, _format: PackageFormat, base_path: Path
    ) -> Optional[PackageFiles]:
        raise NotImplementedError("Subclass must implement this method")


class FilePatternError(Exception):
    pass


class FilePatternNoFilesResolvedError(FilePatternError):
    def __init__(self):
        super().__init__("No files resolved")


class FilePatternInaccessibleError(FilePatternError):
    def __init__(self, path: Path):
        super().__init__(
            f"Source file '{path}' cannot be read: insufficient permissions "
            "or file does not exist"
        )


class FilePattern(BaseModel):
    glob_pattern: Optional[Path] = Field(
        description="Glob pattern to match the files in the built archive"
    )
    path: Path = Field(description="Path where to match the files")

    @model_validator(mode="after")
    def validate_model(self) -> "FilePattern":
        if self.glob_pattern is not None and self.glob_pattern.is_absolute():
            raise ValueError("Glob pattern must be relative")
        if self.glob_pattern is not None and "*" not in str(self.glob_pattern):
            raise ValueError("Invalid glob pattern")
        return self

    def resolve(self, destination_path: Path) -> PackageFiles:
        glob_pattern = self.glob_pattern
        source_path = self.path.resolve()

        base_path = Path.cwd()
        source_path = source_path.relative_to(base_path)

        def is_accessible(path: Path):
            if path.is_symlink():
                symlink = SymbolicLink(path)
                symlink.is_broken()
                symlink.is_escaping(base_path)
                symlink.is_accessible()
                return
            if path.is_file() and path.stat().st_mode & 0o444:
                return
            raise FilePatternInaccessibleError(path)

        def normalize_path(path: Path) -> PackageFile:
            is_accessible(path)
            try:
                relative_path = path.relative_to(base_path)
                return PackageFile(
                    source=relative_path,
                    destination=destination_path / relative_path.relative_to(self.path),
                )
            except ValueError:
                relative_path = Path(base_path / path).relative_to(base_path)
                return PackageFile(
                    source=relative_path,
                    destination=destination_path / relative_path,
                )

        if glob_pattern is None and source_path.is_file():
            is_accessible(source_path)
            return {
                PackageFile(
                    source=source_path,
                    destination=source_path,
                )
            }

        files = []

        str_glob_pattern = str(glob_pattern)
        str_glob_pattern = f"{source_path}/{str_glob_pattern}"

        for source_path in base_path.rglob(str_glob_pattern):
            if not source_path.is_file() and not source_path.is_symlink():
                continue
            if any(part in FORBIDDEN_DIRS for part in source_path.parts):
                continue
            relative_path = normalize_path(source_path)
            files.append(relative_path)

        if len(files) == 0:
            raise FilePatternNoFilesResolvedError()

        return set(files)
