from pathlib import Path
from typing import TYPE_CHECKING, Optional, Self

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from poexy_core.packages.files.collections import FrozenFiles, InclusionFiles
from poexy_core.packages.format import PackageFormat
from poexy_core.packages.package import (
    BinaryPackage,
    ModulePackage,
    SdistPackage,
    WheelPackage,
)
from poexy_core.pyproject.tables.license import License
from poexy_core.pyproject.tables.readme import Readme

if TYPE_CHECKING:
    from poexy_core.packages.files.resolvers.models import PackageResolver


# pylint: disable=no-member


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
    _resolved_package_files: Optional[FrozenFiles] = PrivateAttr(default=None)
    _resolved_inclusions_files: Optional[InclusionFiles] = PrivateAttr(default=None)
    _package_resolver: Optional["PackageResolver"] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.wheel is None:
            # We need a default wheel package configuration to build a wheel.
            # This is useful in api.py to determine which builder to use (whl or binary)
            self.wheel = WheelPackage()
        return self

    def _get_package_resolver(self, _format: PackageFormat) -> "PackageResolver":
        from poexy_core.packages.files.resolvers.models import PackageResolver

        if self._package_resolver is not None:
            return self._package_resolver

        self._package_resolver = PackageResolver(
            format=_format,
            project_path=Path.cwd(),
            source_path=self.package.source,
            poexy=self,
        )

        return self._package_resolver

    def resolve_module_files(self, _format: PackageFormat) -> FrozenFiles:
        if self._resolved_package_files is not None:
            return self._resolved_package_files

        resolver = self._get_package_resolver(_format)

        self._resolved_package_files = resolver.resolve_module_files()

        return self._resolved_package_files

    def resolve_inclusions(self, _format: PackageFormat) -> InclusionFiles:
        if self._resolved_inclusions_files is not None:
            return self._resolved_inclusions_files

        resolver = self._get_package_resolver(_format)

        self._resolved_inclusions_files = resolver.resolve_inclusions()

        return self._resolved_inclusions_files
