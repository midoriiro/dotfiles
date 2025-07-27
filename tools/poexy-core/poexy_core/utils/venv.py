import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List

from poetry.core.packages.dependency import Dependency
from virtualenv import cli_run

from poexy_core.utils import subprocess_rt

logger = logging.getLogger(__name__)


class VirtualEnvironmentError(Exception):
    pass


class VirtualEnvironment:

    def __init__(self, venv_path: Path) -> None:
        self.__venv_path = venv_path
        self.__pip_path = venv_path / "bin" / "pip"
        self.__site_packages_paths = None

    @contextmanager
    @staticmethod
    def create() -> Generator["VirtualEnvironment", None, None]:
        venv_dir = tempfile.TemporaryDirectory()
        venv_path = venv_dir.name

        cli_run([venv_path])

        venv_path = Path(venv_path)
        venv = VirtualEnvironment(venv_path)

        yield venv

        venv_dir.cleanup()

    def install_dependencies(self, dependencies: List[Dependency]) -> None:
        if not self.__pip_path.exists():
            raise VirtualEnvironmentError(f"Pip not found in venv: {self.__pip_path}")

        if not dependencies:
            raise VirtualEnvironmentError("No dependencies to install")

        if len(dependencies) == 0:
            raise VirtualEnvironmentError("No dependencies to install")

        requirements = [dependency.to_pep_508() for dependency in dependencies]

        requirements = " ".join(requirements)

        exit_code = subprocess_rt.run(
            [
                str(self.__pip_path),
                "install",
                requirements,
            ],
            printer=logger.info,
        )

        if exit_code != 0:
            raise VirtualEnvironmentError(
                f"Failed to install dependencies: {exit_code}"
            )

    @property
    def site_packages_paths(self) -> List[Path]:
        if self.__site_packages_paths is None:
            self.__site_packages_paths = []
            for file in self.__venv_path.glob("lib*/python*/site-packages"):
                if file.is_dir() and file.name == "site-packages":
                    self.__site_packages_paths.append(file)
            if len(self.__site_packages_paths) == 0:
                raise VirtualEnvironmentError(
                    f"No site-packages found in venv: {self.__venv_path}"
                )
        return self.__site_packages_paths
