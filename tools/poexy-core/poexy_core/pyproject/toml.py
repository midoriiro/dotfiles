from pathlib import Path
from typing import Any, Dict, Optional, override

from poetry.core.factory import Factory
from poetry.core.poetry import Poetry
from poetry.core.pyproject.tables import BuildSystem
from poetry.core.pyproject.toml import PyProjectTOML as PoetryPyProjectTOML
from pydantic import BaseModel, Field, field_validator

from poexy_core.pyproject.tables.license import License
from poexy_core.pyproject.tables.package import BinaryPackage, ModulePackage
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.pyproject.tables.readme import Readme

# pylint: disable=attribute-defined-outside-init


class PyProjectTOML(BaseModel):
    path: Path = Field(description="Path to the pyproject.toml file")

    @override
    def model_post_init(self, __context: Any, /) -> None:
        self.__data: Dict[str, Any] = PoetryPyProjectTOML(self.path).data
        self.__build_system: Optional[BuildSystem] = None
        self.__poetry: Optional[Poetry] = None
        self.__poexy: Optional[Poexy] = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        path = v / "pyproject.toml"
        if not path.exists():
            raise ValueError(f"Path {v} does not exist")
        if path.name != "pyproject.toml":
            raise ValueError(f"Path {v} is not a pyproject.toml file")
        return path

    @property
    def build_system(self) -> BuildSystem:
        if self.__build_system is None:
            poetry = self.poetry
            pyproject = poetry.pyproject
            package = poetry.package
            # TODO better way to retrieve package name?
            if package.name == "poexy-core":
                dependencies = package.requires
            else:
                dependencies = poetry.build_system_dependencies
            container = pyproject.build_system
            self.__build_system = BuildSystem(
                build_backend=container.build_backend,
                requires=[dependency.to_pep_508() for dependency in dependencies],
            )

        return self.__build_system

    @property
    def poetry(self) -> Poetry:
        if self.__poetry is None:
            self.__poetry = Factory().create_poetry(self.path)
        return self.__poetry

    @property
    def poexy(self) -> Poexy:
        if self.__poexy is None:
            tool = self.__data.get("tool", None)
            if tool is None:
                tool = {}

            assert isinstance(tool, dict)

            poexy_config = tool.get("poexy", None)

            if poexy_config is None:
                poexy_config = {}

            package_config = poexy_config.get("package", None)

            if package_config is None:
                poexy_config.update(ModulePackage.from_project_config(self.__data))
            else:
                poexy_config.update(ModulePackage.from_poexy_config(poexy_config))

            binary_config = poexy_config.get("binary", None)

            if binary_config is None:
                poexy_config.update(BinaryPackage.from_project_config(self.__data))
            else:
                poexy_config.update(BinaryPackage.from_poexy_config(poexy_config))

            readme = Readme.from_project_config(self.__data)
            _license = License.from_project_config(self.__data)

            self.__poexy = Poexy(license=_license, readme=readme, **poexy_config)
        return self.__poexy
