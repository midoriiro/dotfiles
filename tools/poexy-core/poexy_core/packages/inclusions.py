from pathlib import Path
from typing import Any, List, Optional, override

from pydantic import BaseModel, Field, RootModel, model_validator

from poexy_core.packages.files import FilePattern, PackageFiles, ResolvePackageFiles
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.validators import validate_destination
from poexy_core.pyproject.types import GlobPattern

# pylint: disable=no-member


class Exclude(BaseModel, ResolvePackageFiles):
    path: GlobPattern = Field(
        description="Path to exclude from the built archive",
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to exclude. If not specified, all formats "
        "will be excluded.",
    )

    @override
    def resolve(
        self, _format: PackageFormat, base_path: Path
    ) -> Optional[PackageFiles]:
        if self.formats is not None and _format not in self.formats:
            return None
        path, glob_pattern = self.path.split()
        file_pattern = FilePattern(glob_pattern=glob_pattern, path=path)
        if _format == PackageFormat.Source:
            destination_path = path
        else:
            destination_path = base_path
        resolved = file_pattern.resolve(destination_path)
        return resolved


class Include(BaseModel, ResolvePackageFiles):
    path: GlobPattern = Field(description="Path to include in the built archive")
    destination: Optional[Path] = Field(
        description="Relative path to the include path in the built archive",
        default=None,
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to include. If not specified, all formats "
        "will be included.",
    )

    @model_validator(mode="after")
    def validate_model(self) -> "Include":
        if self.destination is not None:
            validate_destination("destination", self.destination)
        return self

    @override
    def resolve(
        self, _format: PackageFormat, base_path: Path
    ) -> Optional[PackageFiles]:
        if self.formats is not None and _format not in self.formats:
            return None
        path, glob_pattern = self.path.split()
        file_pattern = FilePattern(glob_pattern=glob_pattern, path=path)
        if _format == PackageFormat.Source:
            destination_path = path
        elif self.destination is None:
            destination_path = base_path / path
        else:
            destination_path = self.destination / base_path / path
        resolved = file_pattern.resolve(destination_path)
        return resolved


IncludesType = List[Include]
ExcludesType = List[Exclude]


class Includes(RootModel[IncludesType], ResolvePackageFiles):
    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: Any) -> Any:
        if not isinstance(data, list):
            return data
        for index, item in enumerate(data):
            if isinstance(item, str):
                data[index] = Include(path=GlobPattern(pattern=Path(item)))
            else:
                data[index] = Include(
                    path=GlobPattern(pattern=Path(item.get("path"))),
                    destination=item.get("destination", None),
                    formats=item.get("formats", None),
                )
        return data

    @override
    def resolve(
        self, _format: PackageFormat, base_path: Path
    ) -> Optional[PackageFiles]:
        resolved = []
        for item in self.root:
            resolved_item = item.resolve(_format, base_path)
            if resolved_item is not None:
                resolved.extend(resolved_item)
        return set(resolved)


class Excludes(RootModel[ExcludesType], ResolvePackageFiles):
    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, data: Any) -> Any:
        if not isinstance(data, list):
            return data
        for index, item in enumerate(data):
            if isinstance(item, str):
                data[index] = Exclude(path=GlobPattern(pattern=Path(item)))
            else:
                data[index] = Exclude(
                    path=GlobPattern(pattern=Path(item.get("path"))),
                    formats=item.get("formats", None),
                )
        return data

    @override
    def resolve(
        self, _format: PackageFormat, base_path: Path
    ) -> Optional[PackageFiles]:
        resolved = []
        for item in self.root:
            resolved_item = item.resolve(_format, base_path)
            if resolved_item is not None:
                resolved.extend(resolved_item)
        return set(resolved)
