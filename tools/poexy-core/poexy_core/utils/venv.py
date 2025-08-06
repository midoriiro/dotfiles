import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List

from virtualenv import cli_run

from poexy_core.utils.build import Build, BuildOptions
from poexy_core.utils.pip import Pip, PipInstallOptions

logger = logging.getLogger(__name__)


class VirtualEnvironmentError(Exception):
    pass


class VirtualEnvironment:
    def __init__(self, venv_path: Path) -> None:
        self.__venv_path = venv_path
        self.__python_path = venv_path / "bin" / "python"
        self.__pip_path = venv_path / "bin" / "pip"
        self.__site_packages_paths = None
        self._pip = Pip(self.__pip_path)
        self.__builder = Build(self.__python_path)
        self.__build_package_installed = False

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

    def _build(self, source_path: Path) -> Path:
        if not self.__build_package_installed:
            exit_code = self._pip.install(["build"], PipInstallOptions.defaults())
            if exit_code != 0:
                raise VirtualEnvironmentError(f"Failed to install build: {exit_code}")
            self.__build_package_installed = True
        output_path = self.__venv_path / "build"
        if output_path.exists():
            shutil.rmtree(output_path)
        build_options = BuildOptions()
        build_options.wheel(True)
        build_options.output_path(output_path)
        build_options.verbose(True)
        self.__builder.build(source_path, build_options)
        wheel_files = list(output_path.glob("*.whl"))
        if len(wheel_files) == 0:
            raise VirtualEnvironmentError(f"No wheel files found in {output_path}")
        if len(wheel_files) > 1:
            raise VirtualEnvironmentError(
                f"Multiple wheel files found in {output_path}"
            )
        wheel_file = wheel_files[0]
        return wheel_file

    @property
    def path(self) -> Path:
        return self.__venv_path

    @property
    def pip_path(self) -> Path:
        return self.__pip_path

    @property
    def site_packages_paths(self) -> List[Path]:
        if self.__site_packages_paths is None:
            self.__site_packages_paths = []
            for file in self.__venv_path.glob("**/python*/site-packages"):
                if file.is_dir() and file.name == "site-packages":
                    self.__site_packages_paths.append(file)
            if len(self.__site_packages_paths) == 0:
                raise VirtualEnvironmentError(
                    f"No site-packages found in venv: {self.__venv_path}"
                )
        return self.__site_packages_paths
