import logging
from pathlib import Path
from typing import Any, Iterator, List, Optional

from pydantic import BaseModel, Field, RootModel, model_validator

from poexy_core.packages.files.models import PlatformDirectory
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.types import GlobPattern

# pylint: disable=no-member

logger = logging.getLogger(__name__)


class InclusionError(Exception):
    pass


class InclusionNoFilesResolvedError(InclusionError):
    def __init__(self, pattern: str):
        super().__init__(f"No files resolved for pattern '{pattern}'")


class Exclude(BaseModel):
    path: GlobPattern = Field(
        description="Path to exclude from the built archive",
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to apply exclusion. "
        "If not specified, all formats will be applied.",
    )


class Include(BaseModel):
    path: GlobPattern = Field(description="Path to include in the built archive")
    destination: Optional[PlatformDirectory] = Field(
        description="Platform directory to include the file in the built archive",
        default=None,
    )
    formats: Optional[List[PackageFormat]] = Field(
        default=None,
        description="List of package formats to apply inclusion. "
        "If not specified, all formats will be applied.",
    )


IncludesType = List[Include]
ExcludesType = List[Exclude]


class Includes(RootModel[IncludesType]):
    def __len__(self) -> int:
        return len(self.root)

    def __iter__(self) -> Iterator[Include]:
        return iter(self.root)

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


class Excludes(RootModel[ExcludesType]):
    def __len__(self) -> int:
        return len(self.root)

    def __iter__(self) -> Iterator[Include]:
        return iter(self.root)

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
