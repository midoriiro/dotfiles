import logging
import os
import site
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List

from poetry.core.packages.dependency import Dependency
from poetry.core.packages.directory_dependency import DirectoryDependency
from poetry.core.packages.file_dependency import FileDependency
from poetry.core.packages.url_dependency import URLDependency
from poetry.core.packages.vcs_dependency import VCSDependency

from poexy_core.pyproject.toml import DependencyMap
from poexy_core.utils.pip import UvInstallOptions
from poexy_core.utils.venv import VirtualEnvironment, VirtualEnvironmentError

logger = logging.getLogger(__name__)


class PyinstallerVirtualEnvironment(VirtualEnvironment):
    @contextmanager
    @staticmethod
    def create() -> Generator["PyinstallerVirtualEnvironment", None, None]:
        virtual_env = os.environ.get("VIRTUAL_ENV", None)
        prefixes = site.PREFIXES
        if not virtual_env and len(prefixes) == 0:
            raise VirtualEnvironmentError(
                "No virtual environment found. Please run this command from a virtual "
                "environment."
            )

        venv_path = None

        logger.info("Finding virtual environment...")

        if virtual_env:
            logger.info(f"Using virtual environment from VIRTUAL_ENV: {virtual_env}")
            venv_path = virtual_env
        else:
            if len(prefixes) == 1:
                logger.info(
                    f"Using virtual environment from site.PREFIXES: {prefixes[0]}"
                )
                venv_path = prefixes[0]
            elif len(prefixes) > 1:
                raise VirtualEnvironmentError(
                    "Multiple virtual environments found. Please run this command from "
                    "a specific virtual environment."
                )

        venv_path = Path(venv_path)
        venv = PyinstallerVirtualEnvironment(venv_path)

        yield venv

    def install_dependencies(
        self, dependencies: DependencyMap
    ) -> List[DirectoryDependency]:
        if not self.pip_path.exists():
            raise VirtualEnvironmentError(f"Pip not found in venv: {self.pip_path}")

        if not dependencies:
            raise VirtualEnvironmentError("No dependencies to install")

        if len(dependencies) == 0:
            raise VirtualEnvironmentError("No dependencies to install")

        requirements = []
        directory_dependencies = []
        for _, deps in dependencies.items():
            dependency_types = [dependency.__class__.__name__ for dependency in deps]
            if Dependency.__name__ in dependency_types:
                dependency: Dependency = next(
                    filter(
                        lambda dependency: isinstance(dependency, Dependency),
                        deps,
                    )
                )
                if dependency.source_type is not None:
                    raise VirtualEnvironmentError(
                        f"Expected a public dependency, got '{dependency.source_type}'"
                    )
                requirements.append(dependency.to_pep_508())
            elif URLDependency.__name__ in dependency_types:
                dependency: URLDependency = next(
                    filter(
                        lambda dependency: isinstance(dependency, URLDependency),
                        deps,
                    )
                )
                if dependency.source_type != "url":
                    raise VirtualEnvironmentError("Expected an url dependency")
                requirements.append(dependency.source_url)
            elif VCSDependency.__name__ in dependency_types:
                dependency: VCSDependency = next(
                    filter(
                        lambda dependency: isinstance(dependency, VCSDependency),
                        deps,
                    )
                )
                requirements.append(dependency.to_pep_508())
            elif FileDependency.__name__ in dependency_types:
                dependency: FileDependency = next(
                    filter(
                        lambda dependency: isinstance(dependency, FileDependency),
                        deps,
                    )
                )
                if dependency.source_type != "file":
                    raise VirtualEnvironmentError("Expected a file dependency")
                requirements.append(dependency.full_path.as_posix())
            elif DirectoryDependency.__name__ in dependency_types:
                dependency: DirectoryDependency = next(
                    filter(
                        lambda dependency: isinstance(dependency, DirectoryDependency),
                        deps,
                    )
                )
                if dependency.source_type != "directory":
                    raise VirtualEnvironmentError(
                        "Expected a directory dependency pointing to a directory"
                    )
                directory_dependencies.append(dependency)

        if len(requirements) == 0:
            return directory_dependencies

        install_options = UvInstallOptions()
        install_options.no_build_isolation(True)
        install_options.reinstall(True)
        install_options.verbose(True)
        install_options.no_config(True)

        exit_code = self._pip.install(requirements, install_options)

        if exit_code != 0:
            raise VirtualEnvironmentError(
                f"Failed to install dependencies: {exit_code}"
            )

        return directory_dependencies
