import json
import logging
from pathlib import Path

from virtualenv import cli_run

from poexy_core.utils import subprocess_rt
from poexy_core.utils.pip import PackageInstallerProgram
from poexy_core.utils.venv import VirtualEnvironment, VirtualEnvironmentError

logger = logging.getLogger(__name__)


class TestVirtualEnvironment(VirtualEnvironment):
    __test__ = False

    def __init__(self, venv_path: Path):
        super().__init__(venv_path)
        self.__site_package_path = None

    @staticmethod
    def create_from_path(venv_path: Path) -> "TestVirtualEnvironment":
        cli_run([str(venv_path)])
        return TestVirtualEnvironment(venv_path)

    @staticmethod
    def create_from_archive(
        archive_path: Path, venv_path: Path
    ) -> "TestVirtualEnvironment":
        TestVirtualEnvironment.__extract_archive(archive_path, venv_path)
        return TestVirtualEnvironment(venv_path)

    @property
    def pip(self) -> PackageInstallerProgram:
        return self._pip

    @property
    def site_package(self) -> Path:
        if self.__site_package_path is None:
            for file in self.path.glob("lib/python*/site-packages"):
                if file.is_dir() and file.name == "site-packages":
                    self.__site_package_path = file
                    return file
            raise VirtualEnvironmentError(
                f"No site-packages found in venv: {self.__venv_path}"
            )
        return self.__site_package_path

    @property
    def bin_path(self) -> Path:
        return self.path / "bin"

    @staticmethod
    def archive_name() -> str:
        return "venv.tar.zst"

    def build(self, source_path: Path) -> Path:
        return self._build(source_path)

    def create_archive(self, archive_path: Path) -> Path:
        venv_config = {
            "base_path": str(self.path),
            "created_at": str(Path().stat().st_mtime),
        }
        with open(self.path / "venv.json", "w", encoding="utf-8") as f:
            json.dump(venv_config, f)

        cmd = [
            "tar",
            "--use-compress-program",
            "zstd",
            "--create",
            "--file",
            str(archive_path / TestVirtualEnvironment.archive_name()),
            "--directory",
            str(self.path),
            ".",
        ]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise VirtualEnvironmentError(f"Failed to create venv archive: {exit_code}")
        return archive_path / TestVirtualEnvironment.archive_name()

    @staticmethod
    def __extract_archive(archive_path: Path, venv_path: Path) -> None:
        cmd = [
            "rm",
            "-rf",
            str(venv_path),
        ]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise VirtualEnvironmentError(f"Failed to remove venv: {exit_code}")
        venv_path.mkdir(parents=True, exist_ok=True)
        cmd = [
            "tar",
            "--use-compress-program",
            "zstd",
            "--extract",
            "--file",
            str(archive_path),
            "--directory",
            str(venv_path),
        ]
        logger.info(f"Extracting venv archive: {archive_path}")
        exit_code = subprocess_rt.run(cmd, printer=logger.info)

        if exit_code != 0:
            raise VirtualEnvironmentError(
                f"Failed to extract venv archive: {exit_code}"
            )

        TestVirtualEnvironment.__upgrade_scripts_shebang(venv_path)

    @staticmethod
    def __upgrade_scripts_shebang(venv_path: Path) -> None:
        with open(venv_path / "venv.json", "r", encoding="utf-8") as f:
            venv_config = json.load(f)

        bin_path = venv_path / "bin"
        if not bin_path.exists():
            return

        binary_files = []

        for file in bin_path.iterdir():
            if file.is_file() and not file.is_symlink() and file.stat().st_mode & 0o111:
                binary_files.append(file)

        for file in binary_files:
            try:
                content = file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            logger.info(f"Upgrading shebang for script: {file}")
            if venv_config["base_path"] in content:
                file.write_text(
                    content.replace(venv_config["base_path"], str(venv_path)),
                    encoding="utf-8",
                )
