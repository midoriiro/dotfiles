import logging
import shutil
import sys
from pathlib import Path
from typing import Any, List, Optional

from poetry.core.masonry.metadata import Metadata
from poetry.core.poetry import Poetry

from poexy_core.builders.hooks.hook import HookBuilder
from poexy_core.manifest.manifest import Manifest
from poexy_core.metadata.builder import MetadataManifestBuilder
from poexy_core.metadata.fields import MetadataVersions
from poexy_core.packages.format import PackageFormat
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.utils import python_impl

logger = logging.getLogger(__name__)


class PythonTag:
    def __init__(
        self,
        impl: Optional[str] = None,
        major: Optional[int] = None,
        minor: Optional[int] = None,
        abi: Optional[str] = None,
        platform: Optional[str] = None,
    ):
        self.impl: Optional[str] = impl
        self.major: Optional[int] = major
        self.minor: Optional[int] = minor
        self.platform: Optional[str] = platform
        self.abi: Optional[str] = abi

    @staticmethod
    def from_current_environment() -> "PythonTag":
        return PythonTag(
            impl=python_impl.get_python_implementation_tag(),
            major=sys.version_info.major,
            minor=sys.version_info.minor,
            abi=python_impl.get_abi_tag(),
            platform=python_impl.get_platform_tag(),
        )

    def __eq__(self, other: "PythonTag") -> bool:
        return str(self) == str(other)

    def __ne__(self, other: "PythonTag") -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __str__(self) -> str:
        if self.impl is None:
            impl = "py"
        else:
            impl = self.impl

        if self.major is None:
            major = sys.version_info.major
        else:
            major = self.major

        if self.minor is None:
            minor = sys.version_info.minor
        else:
            minor = self.minor

        if self.minor is None:
            python_tag = f"{impl}{major}"
        else:
            python_tag = f"{impl}{major}{minor}"

        if self.abi is None:
            abi_tag = "none"
        else:
            abi_tag = self.abi

        if self.platform is None:
            platform_tag = "any"
        else:
            platform_tag = self.platform.replace("-", "_").replace(".", "_")

        tag = f"{python_tag}-{abi_tag}-{platform_tag}"

        return tag


class Builder:
    def __init__(
        self,
        poetry: Poetry,
        poexy: Poexy,
        _format: PackageFormat,
        destination_directory: Path,
        config_settings: dict[str, Any] | None = None,
    ):
        self.poetry = poetry
        self.poexy = poexy
        self.format = _format
        self.destination_directory = destination_directory
        self.temp_destination_directory = destination_directory / "temp"
        self.config_settings = config_settings
        self.package_name = self.poetry.package.name
        self.package_version = self.poetry.package.version

        shutil.rmtree(self.temp_destination_directory, ignore_errors=True)

        if not self.destination_directory.exists():
            self.destination_directory.mkdir(parents=True, exist_ok=True)

        if not self.temp_destination_directory.exists():
            self.temp_destination_directory.mkdir(parents=True, exist_ok=True)

        self._hooks: List[HookBuilder] = []

    def add_hook(self, hook: HookBuilder):
        self._hooks.append(hook)

    def _add_metadata(self, manifest: Manifest) -> MetadataManifestBuilder:
        if self.poexy.readme is not None:
            self.poexy.readme.transform_poetry_package(self.poetry.package)
        metadata = Metadata.from_package(self.poetry.package)
        for hook in self._hooks:
            hook.add_metadata(metadata, self.format)
        builder = MetadataManifestBuilder(manifest, MetadataVersions.V2_4)
        MetadataManifestBuilder.from_poetry(builder, metadata)
        return builder

    def build(self) -> Path:
        raise NotImplementedError("Subclass must implement build method")
