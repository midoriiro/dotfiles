from pathlib import Path
from typing import List, Optional, Self, Set

from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.format import (
    DEFAULT_FORMATS,
    DEFAULT_WHEEL_FORMATS,
    PackageFormat,
    WheelFormat,
)
from poexy_core.packages.inclusions import Excludes, Includes
from poexy_core.packages.validators import validate_path

# pylint: disable=no-member


class BasePackage(BaseModel):
    includes: Optional[Includes] = Field(
        description="List of includes in package", default=None
    )
    excludes: Optional[Excludes] = Field(
        description="List of excludes in package", default=None
    )
    _is_format_allowed: bool = False
    _default_formats: List[PackageFormat]

    @model_validator(mode="after")
    def validate_package(self) -> Self:
        if self.includes is not None:
            for include in self.includes:
                if include.formats is not None and not self._is_format_allowed:
                    raise ValueError("formats are not allowed in includes")
                if include.formats is None:
                    include.formats = self._default_formats
        if self.excludes is not None:
            for exclude in self.excludes:
                if exclude.formats is not None and not self._is_format_allowed:
                    raise ValueError("formats are not allowed in excludes")
                if exclude.formats is None:
                    exclude.formats = self._default_formats
        return self


class ModulePackage(BasePackage):
    _is_format_allowed: bool = True
    _default_formats: List[PackageFormat] = DEFAULT_FORMATS

    name: str = Field(description="Name of the package")
    source: Optional[Path] = Field(
        description="Source path if it differs from the name of the package",
        default=None,
    )

    @model_validator(mode="after")
    def validate_module_package(self) -> Self:
        if self.includes is not None:
            for include in self.includes.root:
                if include.formats is None:
                    include.formats = self._default_formats
        if self.excludes is not None:
            for exclude in self.excludes.root:
                if exclude.formats is None:
                    exclude.formats = self._default_formats
        if self.source is not None:
            self.source = validate_path("source", self.source)
        else:
            self.source = Path(self.name)
        if not self.source.resolve().is_relative_to(Path.cwd().absolute()):
            raise ValueError("Source path is outside the root project directory")
        if not any(self.source.iterdir()):
            raise ValueError("Source path is empty")
        return self


class WheelPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Wheel]

    format: Set[WheelFormat] = Field(
        description="Formats of the wheel",
        default=set(DEFAULT_WHEEL_FORMATS),
        min_length=1,
        max_length=2,
    )


class SdistPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Source]


class BinaryPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Binary]

    name: Optional[str] = Field(
        default=None,
        min_length=3,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_-]+$",
        description="Name of the executable",
    )

    entry_point: Optional[str] = Field(
        default=None,
        pattern=r"^([a-zA-Z][a-zA-Z0-9_.]+|\.)?$",
        description="Entry point of the package",
    )

    @model_validator(mode="after")
    def validate_binary_package(self) -> Self:
        if self.entry_point is not None:
            entry_point = Path(self.entry_point.replace(".", "/") + ".py")
            if not entry_point.exists():
                raise ValueError(f"Entry point {entry_point} does not exist")
            self.entry_point = str(entry_point)
        return self
