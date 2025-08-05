from pathlib import Path
from typing import Any, Dict, List, Optional, override

from poetry.core.factory import Factory
from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.poetry import Poetry
from poetry.core.pyproject.tables import BuildSystem
from poetry.core.pyproject.toml import PyProjectTOML as PoetryPyProjectTOML
from pydantic import BaseModel, Field, field_validator

from poexy_core.pyproject.exceptions import PyProjectError
from poexy_core.pyproject.tables.license import License
from poexy_core.pyproject.tables.package import BinaryPackage, ModulePackage
from poexy_core.pyproject.tables.poexy import Poexy
from poexy_core.pyproject.tables.readme import Readme

# pylint: disable=attribute-defined-outside-init

DependencyMap = Dict[str, List[Dependency]]


class PyProjectTOML(BaseModel):
    path: Path = Field(description="Path to the pyproject.toml file")

    @override
    def model_post_init(self, __context: Any, /) -> None:
        self.__data: Dict[str, Any] = PoetryPyProjectTOML(self.path).data
        self.__build_system: Optional[BuildSystem] = None
        self.__poetry: Optional[Poetry] = None
        self.__poexy: Optional[Poexy] = None
        self.__dependencies: Optional[Dict[str, List[Dependency]]] = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Path) -> Path:
        path = v / "pyproject.toml"
        if not path.exists():
            raise ValueError(f"Path {v} does not exist")
        if path.name != "pyproject.toml":
            raise ValueError(f"Path {v} is not a pyproject.toml file")
        return path

    def validate_dependencies(self) -> None:
        dependencies = self.dependencies
        for key, values in dependencies.items():
            dependency_types = [dependency.__class__.__name__ for dependency in values]
            if (
                FileDependency.__name__ in dependency_types
                and DirectoryDependency.__name__ in dependency_types
            ):
                raise PyProjectError(
                    f"Dependency '{key}' is pointing only to local dependencies. "
                    "This is not allowed and you should provide alternative "
                    "dependency types other than file or directory."
                )
            for dependency in values:
                dependency_name = dependency.name
                if isinstance(dependency, DirectoryDependency) and len(values) == 1:
                    raise PyProjectError(
                        f"Dependency '{dependency_name}' is pointing to a directory. "
                        "This is not allowed and you should provide alternative "
                        "dependency types other than file or directory."
                    )
                elif isinstance(dependency, FileDependency) and len(values) == 1:
                    if dependency.source_type == "file":
                        raise PyProjectError(
                            f"Dependency '{dependency_name}' is pointing to a file. "
                            "This is not allowed and you should provide alternative "
                            "dependency types other than file or directory."
                        )

    @staticmethod
    def dependencies_from_poetry(poetry: Poetry) -> DependencyMap:
        dependencies = poetry.package.requires
        dependencies_map: DependencyMap = {}
        for dependency in dependencies:
            if dependency.name in dependencies_map:
                dependencies_map[dependency.name].append(dependency)
            else:
                dependencies_map[dependency.name] = [dependency]
        return dependencies_map

    @property
    def dependencies(self) -> DependencyMap:
        if self.__dependencies is None:
            self.__dependencies = self.dependencies_from_poetry(self.poetry)
        return self.__dependencies

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
