from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.files import ResolvedPackageFiles
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.package import BinaryPackage, ModulePackage, SdistPackage, WheelPackage

class Poexy(BaseModel):
    package: ModulePackage = Field(
        description="Package to include in the built archive"
    )
    wheel: Optional[WheelPackage] = Field(
        description="Wheel package configuration",
        default=None
    )
    sdist: Optional[SdistPackage] = Field(
        description="Sdist package configuration",
        default=None
    )
    binary: Optional[BinaryPackage] = Field(
        description="Binary package configuration",
        default=None
    )

    @model_validator(mode="after")
    def validate(self) -> "Poexy":
        if self.wheel is None:
            self.wheel = WheelPackage()
        return self
    
    def resolve(self, format: PackageFormat) -> ResolvedPackageFiles:
        includes = []
        excludes = []
        base_path = Path(self.package.name)
        includes.extend(self.package.resolve_includes(format, base_path))
        if self.package.excludes is not None:
            excludes.extend(self.package.resolve_excludes(format, base_path))
        if self.wheel is not None and format in PackageFormat.Wheel:
            if self.wheel.includes is not None:
                includes.extend(self.wheel.resolve_includes(format, base_path))
            if self.wheel.excludes is not None:
                excludes.extend(self.wheel.resolve_excludes(format, base_path))
        if self.sdist is not None and format in PackageFormat.Source:
            if self.sdist.includes is not None:
                includes.extend(self.sdist.resolve_includes(format, base_path))
            if self.sdist.excludes is not None:
                excludes.extend(self.sdist.resolve_excludes(format, base_path))
        if self.binary is not None and format in PackageFormat.Binary:
            if self.binary.includes is not None:
                includes.extend(self.binary.resolve_includes(format, base_path))
            if self.binary.excludes is not None:
                excludes.extend(self.binary.resolve_excludes(format, base_path))
        return ResolvedPackageFiles(
            includes=includes,
            excludes=excludes
        )
