import json
import os
from pathlib import Path
from typing import Optional

from poexy_core.utils import subprocess_rt


class Pip:
    def __init__(self, virtualenv_path: Path):
        self.__virtualenv_path = virtualenv_path
        self.__virtualenv_path.mkdir(parents=True, exist_ok=True)
        self.__cache_path = virtualenv_path / ".cache"
        self.__cache_path.mkdir(parents=True, exist_ok=True)
        self.__common_args = [
            # "--verbose",
            "--require-virtualenv",
            "--isolated",
            "--cache-dir",
            str(self.__cache_path),
        ]

    def __create_virtualenv(self) -> int:
        cmd = [
            "poetry",
            "run",
            "virtualenv",
            "--always-copy",
            "--seeder",
            "app-data",
            "--no-download",
            "--no-setuptools",
            str(self.__virtualenv_path),
        ]
        exit_code = subprocess_rt.run(cmd, printer=print)
        return exit_code

    def __get_pip_path(self) -> Path:
        return self.__virtualenv_path / "bin" / "pip"

    def __execute_pip_command(self, cmd: list[str]) -> int:
        cmd = [str(self.__get_pip_path()), *cmd]
        env = os.environ.copy()
        exit_code = subprocess_rt.run(cmd, printer=print, env=env)
        return exit_code

    def __upgrade_scripts_shebang(self) -> None:
        with open(self.__virtualenv_path / "venv.json", "r", encoding="utf-8") as f:
            venv_config = json.load(f)

        bin_path = self.__virtualenv_path / "bin"
        if not bin_path.exists():
            return

        binary_files = [
            f for f in bin_path.iterdir() if f.is_file() and f.stat().st_mode & 0o111
        ]

        for file in binary_files:
            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if venv_config["base_path"] in content:
                file.write_text(
                    content.replace(
                        venv_config["base_path"], str(self.__virtualenv_path)
                    ),
                    encoding="utf-8",
                )

    def create_virtualenv(self) -> None:
        exit_code = self.__create_virtualenv()
        if exit_code != 0:
            raise RuntimeError(f"Failed to create virtualenv: {exit_code}")

    def create_virtualenv_archive(self, archive_path: Path) -> Path:
        archive_name = "venv.tar.zst"

        venv_config = {
            "base_path": str(self.__virtualenv_path),
            "created_at": str(Path().stat().st_mtime),
        }
        with open(self.__virtualenv_path / "venv.json", "w", encoding="utf-8") as f:
            json.dump(venv_config, f)

        cmd = [
            "tar",
            "--use-compress-program",
            "zstd",
            "--create",
            "--file",
            str(archive_path / archive_name),
            "--directory",
            str(self.__virtualenv_path),
            ".",
        ]
        exit_code = subprocess_rt.run(cmd, printer=print)
        if exit_code != 0:
            raise RuntimeError(f"Failed to create virtualenv archive: {exit_code}")
        return archive_path / archive_name

    def extract_virtualenv_archive(self, archive_path: Path) -> None:
        cmd = [
            "rm",
            "-rf",
            str(self.__virtualenv_path),
        ]
        exit_code = subprocess_rt.run(cmd, printer=print)
        if exit_code != 0:
            raise RuntimeError(f"Failed to remove virtualenv: {exit_code}")
        self.__virtualenv_path.mkdir(parents=True, exist_ok=True)
        cmd = [
            "tar",
            "--use-compress-program",
            "zstd",
            "--extract",
            "--file",
            str(archive_path),
            "--directory",
            str(self.__virtualenv_path),
        ]
        exit_code = subprocess_rt.run(cmd, printer=print)

        if exit_code != 0:
            raise RuntimeError(f"Failed to extract virtualenv archive: {exit_code}")

        self.__upgrade_scripts_shebang()

    def wheel(
        self,
        archive_path: Path,
        wheel_directory: Optional[Path] = None,
        no_build_isolation: bool = True,
        check_build_dependencies: bool = True,
    ) -> int:
        cmd = ["wheel"]
        if wheel_directory is not None:
            cmd.extend(["--wheel-dir", str(wheel_directory)])
        if no_build_isolation:
            cmd.append("--no-build-isolation")
        if check_build_dependencies:
            cmd.append("--check-build-dependencies")
        cmd.extend(["--use-pep517", "--no-clean"])
        cmd.extend(self.__common_args)
        cmd.append(str(archive_path))
        return self.__execute_pip_command(cmd)

    def install(
        self,
        archive_path: Path,
        install_directory: Optional[Path] = None,
        no_build_isolation: bool = True,
        check_build_dependencies: bool = True,
    ) -> int:
        cmd = [
            "install",
        ]
        if install_directory is not None:
            cmd.append("--prefix")
            cmd.append(str(install_directory))
        if no_build_isolation:
            cmd.append("--no-build-isolation")
        if check_build_dependencies:
            cmd.append("--check-build-dependencies")
            cmd.extend(self.__common_args)
        cmd.extend(["--use-pep517", "--no-clean", "--force-reinstall"])
        cmd.extend(self.__common_args)
        cmd.append(str(archive_path))
        return self.__execute_pip_command(cmd)

    def uninstall(self, package_name: str) -> int:
        cmd = ["uninstall", "--yes"]
        cmd.extend(self.__common_args)
        cmd.append(package_name)
        return self.__execute_pip_command(cmd)

    def show(self, package_name: str) -> int:
        cmd = ["show"]
        cmd.extend(self.__common_args)
        cmd.append(package_name)
        return self.__execute_pip_command(cmd)
