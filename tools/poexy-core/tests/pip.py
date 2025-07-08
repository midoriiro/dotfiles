from pathlib import Path
import subprocess
from typing import Generator, Optional, Tuple

from poexy_core.utils import subprocess_rt

class Pip:
    def __init__(self, virtualenv_path: Path):
        self.__virtualenv_path = virtualenv_path

    def __create_virtualenv(self) -> int:
        cmd = [
            "poetry",
            "run",
            "python",
            "-m",
            "venv",
            str(self.__virtualenv_path)
        ]
        exit_code = subprocess_rt.run(cmd, printer=lambda x: print(x))
        return exit_code
    
    def __get_pip_path(self) -> Path:
        return self.__virtualenv_path / "bin" / "pip"

    def __execute_pip_command(self, cmd: list[str]) -> int:
        cmd = [
            str(self.__get_pip_path()),
            *cmd
        ]
        exit_code = subprocess_rt.run(cmd, printer=lambda x: print(x))
        return exit_code
    
    def create_virtualenv(self) -> None:
        exit_code = self.__create_virtualenv()
        if exit_code != 0:
            raise RuntimeError(f"Failed to create virtualenv: {exit_code}")

    def wheel(
        self,
        archive_path: Path,
        wheel_directory: Optional[Path] = None
    ) -> Tuple[int, str]:
        cmd = [
            "wheel", 
        ]
        if wheel_directory is not None:
            cmd.append("--wheel-dir")
            cmd.append(str(wheel_directory))
        cmd.extend([
            "--use-pep517",
            "--check-build-dependencies",
            "--no-build-isolation",
            "--no-clean",
            # "--debug",
            "--verbose",
            str(archive_path)
        ])
        return self.__execute_pip_command(cmd)
    
    def install(
        self,
        archive_path: Path,
        install_directory: Optional[Path] = None
    ) -> Tuple[int, str]:
        cmd = [
            "install", 
        ]
        if install_directory is not None:
            cmd.append("--prefix")
            cmd.append(str(install_directory))
        cmd.extend([
            "--force-reinstall",
            "--use-pep517",
            "--check-build-dependencies",
            "--no-build-isolation",
            "--no-clean",
            # "--debug",
            "--verbose",
            str(archive_path)
        ])
        return self.__execute_pip_command(cmd)