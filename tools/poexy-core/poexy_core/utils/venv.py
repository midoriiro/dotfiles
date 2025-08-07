import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List

from virtualenv import cli_run

from poexy_core.utils.build import BuildOptions, UvBuild
from poexy_core.utils.pip import PackageInstallerProgram, Pip, Uv

logger = logging.getLogger(__name__)


class VirtualEnvironmentError(Exception):
    pass


class VirtualEnvironment:
    def __init__(self, venv_path: Path) -> None:
        self.__venv_path = venv_path
        self.__python_path = venv_path / "bin" / "python"
        self.__pip_path = venv_path / "bin" / "pip"
        self.__uv_path = venv_path / "bin" / "uv"
        self.__site_packages_paths = None
        self._pip: PackageInstallerProgram = Uv(
            self.__python_path, self.__uv_path, Pip(self.__pip_path)
        )
        self.__builder = UvBuild(self.__uv_path)

        if not self.__venv_path.exists():
            raise VirtualEnvironmentError(f"venv not found in {self.__venv_path}")

        if not self.__python_path.exists():
            raise VirtualEnvironmentError(f"python not found in {self.__python_path}")

        if not self.__pip_path.exists():
            raise VirtualEnvironmentError(f"pip not found in {self.__pip_path}")

        if not self.__uv_path.exists():
            raise VirtualEnvironmentError(f"uv not found in {self.__uv_path}")

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
        output_path = self.__venv_path / "build"
        if output_path.exists():
            shutil.rmtree(output_path)
        build_options = BuildOptions()
        build_options.verbose(True)
        build_options.no_config(True)
        build_options.python_interpreter(self.__python_path)
        build_options.wheel(True)
        build_options.output_path(output_path)
        build_options.force_pep517(True)
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
