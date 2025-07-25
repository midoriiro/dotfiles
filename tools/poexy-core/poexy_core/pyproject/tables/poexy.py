from pathlib import Path
from typing import Any, List, Optional, override

from pydantic import BaseModel, Field, model_validator

from poexy_core.packages.files import PackageFile, PackageFiles, ResolvedPackageFiles
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.package import (
    BinaryPackage,
    ModulePackage,
    SdistPackage,
    WheelPackage,
)
from poexy_core.pyproject.tables.license import License
from poexy_core.pyproject.tables.readme import Readme

# pylint: disable=no-member,attribute-defined-outside-init


class Poexy(BaseModel):
    package: ModulePackage = Field(
        description="Package to include in the built archive"
    )
    wheel: Optional[WheelPackage] = Field(
        description="Wheel package configuration", default=None
    )
    sdist: Optional[SdistPackage] = Field(
        description="Sdist package configuration", default=None
    )
    binary: Optional[BinaryPackage] = Field(
        description="Binary package configuration", default=None
    )
    readme: Optional[Readme] = Field(description="Readme configuration", default=None)
    license: Optional[License] = Field(
        description="License configuration", default=None
    )

    @override
    def model_post_init(self, __context: Any, /) -> None:
        self.__resolved_package_files: Optional[PackageFiles] = None
        self.__resolved_inclusions_files: Optional[ResolvedPackageFiles] = None

    @model_validator(mode="after")
    def validate_model(self) -> "Poexy":
        if self.wheel is None:
            # We need a default wheel package configuration to build a wheel.
            # This is useful in api.py to determine which builder to use (whl or binary)
            self.wheel = WheelPackage()
        return self

    def resolve_package_files(self, _format: PackageFormat) -> PackageFiles:
        if self.__resolved_package_files is None:
            base_path = Path(self.package.name)
            resolved_files = self.package.resolve(_format, base_path)
            if resolved_files is None:
                raise ValueError("No package files found")
            self.__resolved_package_files = resolved_files
        return self.__resolved_package_files

    def resolve_inclusions(self, _format: PackageFormat) -> ResolvedPackageFiles:
        if self.__resolved_inclusions_files is None:
            includes: List[PackageFile] = []
            excludes: List[PackageFile] = []
            base_path = Path(self.package.name)
            if self.package.includes is not None:
                resolved_files = self.package.resolve_includes(_format, base_path)
                if resolved_files is not None:
                    includes.extend(resolved_files)
            if self.package.excludes is not None:
                resolved_files = self.package.resolve_excludes(_format, base_path)
                if resolved_files is not None:
                    excludes.extend(resolved_files)
            if self.wheel is not None and _format in PackageFormat.Wheel:
                if self.wheel.includes is not None:
                    resolved_files = self.wheel.resolve_includes(_format, base_path)
                    if resolved_files is not None:
                        includes.extend(resolved_files)
                if self.wheel.excludes is not None:
                    resolved_files = self.wheel.resolve_excludes(_format, base_path)
                    if resolved_files is not None:
                        excludes.extend(resolved_files)
            if self.sdist is not None and _format in PackageFormat.Source:
                if self.sdist.includes is not None:
                    resolved_files = self.sdist.resolve_includes(_format, base_path)
                    if resolved_files is not None:
                        includes.extend(resolved_files)
                if self.sdist.excludes is not None:
                    resolved_files = self.sdist.resolve_excludes(_format, base_path)
                    if resolved_files is not None:
                        excludes.extend(resolved_files)
            if self.binary is not None and _format in PackageFormat.Binary:
                if self.binary.includes is not None:
                    resolved_files = self.binary.resolve_includes(_format, base_path)
                    if resolved_files is not None:
                        includes.extend(resolved_files)
                if self.binary.excludes is not None:
                    resolved_files = self.binary.resolve_excludes(_format, base_path)
                    if resolved_files is not None:
                        excludes.extend(resolved_files)
            self.__resolved_inclusions_files = ResolvedPackageFiles(
                includes=set(includes), excludes=set(excludes)
            )
        return self.__resolved_inclusions_files
