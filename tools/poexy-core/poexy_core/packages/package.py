from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, override
from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.files import FilePattern, PackageFiles, ResolvePackageFiles
from poexy_core.packages.format import DEFAULT_FORMATS, DEFAULT_WHEEL_FORMATS, PackageFormat, WheelFormat
from poexy_core.packages.inclusions import Excludes, Includes
from poexy_core.packages.validators import extract_path_and_glob_pattern, validate_path


class BasePackage(BaseModel):
    includes: Optional[Includes] = Field(
        description="List of includes in package",
        default=None
    )
    excludes: Optional[Excludes] = Field(
        description="List of excludes in package",
        default=None
    )
    _is_format_allowed: bool = False
    _default_formats: List[PackageFormat]

    @model_validator(mode="after")
    def validate(self) -> "BasePackage":
        if self.includes is not None:
            for include in self.includes.root:
                if include.formats is not None and self._is_format_allowed == False:
                    raise ValueError("formats are not allowed in includes")
                if include.formats is None:
                    include.formats = self._default_formats
        if self.excludes is not None:
            for exclude in self.excludes.root:
                if exclude.formats is not None and self._is_format_allowed == False:
                    raise ValueError("formats are not allowed in excludes")
                if exclude.formats is None:
                    exclude.formats = self._default_formats
        return self
    
    def resolve_includes(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        if self.includes is None:
            return None
        return self.includes.resolve(format, base_path)
    
    def resolve_excludes(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        if self.excludes is None:
            return None
        return self.excludes.resolve(format, base_path)
        
    
class ModulePackage(BasePackage, ResolvePackageFiles):
    _is_format_allowed: bool = True
    _default_formats: List[PackageFormat] = DEFAULT_FORMATS

    name: str = Field(
        description="Name of the package"
    )
    source: Optional[Path] = Field(
        description="Source path if it differs from the name of the package",
        default=None
    )

    @model_validator(mode="after")
    def validate(self) -> "ModulePackage":
        super().validate()
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
        return self
    
    @override
    def resolve(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        path, glob_pattern = extract_path_and_glob_pattern("source", self.source)
        file_pattern = FilePattern(
            glob_pattern=glob_pattern,
            path=path
        )
        if format == PackageFormat.Source:
            destination_path = path
        else:
            destination_path = Path(self.name)
        resolved = file_pattern.resolve(destination_path)
        return resolved
    
    @override
    def resolve_includes(self, format: PackageFormat, base_path: Path) -> Optional[PackageFiles]:
        resolved = []
        resolved.extend(self.resolve(format, base_path))
        if self.includes is not None:
            resolved.extend(super().resolve_includes(format, base_path))
        return set(resolved)

class WheelPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Wheel]

    format: Set[WheelFormat] = Field(
        description="Formats of the wheel",
        default=DEFAULT_WHEEL_FORMATS,
        min_length=1,
        max_length=len(WheelFormat._member_map_.values())
    )

    
class SdistPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Source]

    
class BinaryPackage(BasePackage):
    _default_formats: List[PackageFormat] = [PackageFormat.Binary]

    name: Optional[str] = Field(
        default=None,
        min_length=3,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_-]+$",
        description="Name of the executable"
    )

    entry_point: Optional[str] = Field(
        default=None,
        pattern=r"^([a-zA-Z][a-zA-Z0-9_.]+|\.)(:[a-zA-Z0-9_]+)?$",
        description="Entry point of the package"
    )

    