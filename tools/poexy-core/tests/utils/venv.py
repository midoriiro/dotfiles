import json
import logging
from pathlib import Path

from virtualenv import cli_run

from poexy_core.utils import subprocess_rt
from poexy_core.utils.pip import Pip
from poexy_core.utils.venv import VirtualEnvironment, VirtualEnvironmentError

logger = logging.getLogger(__name__)


class TestVirtualEnvironment(VirtualEnvironment):
    def __init__(self, venv_path: Path):
        super().__init__(venv_path)
        self.__site_package_path = None

    @staticmethod
    def create_from(venv_path: Path) -> "TestVirtualEnvironment":
        cli_run([str(venv_path)])
        return TestVirtualEnvironment(venv_path)

    @property
    def pip(self) -> Pip:
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

    def build(self, source_path: Path) -> Path:
        return self._build(source_path)

    def create_archive(self, archive_path: Path) -> Path:
        archive_name = "venv.tar.zst"

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
            str(archive_path / archive_name),
            "--directory",
            str(self.path),
            ".",
        ]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise VirtualEnvironmentError(f"Failed to create venv archive: {exit_code}")
        return archive_path / archive_name

    def extract_archive(self, archive_path: Path) -> None:
        cmd = [
            "rm",
            "-rf",
            str(self.path),
        ]
        exit_code = subprocess_rt.run(cmd, printer=logger.info)
        if exit_code != 0:
            raise VirtualEnvironmentError(f"Failed to remove venv: {exit_code}")
        self.path.mkdir(parents=True, exist_ok=True)
        cmd = [
            "tar",
            "--use-compress-program",
            "zstd",
            "--extract",
            "--file",
            str(archive_path),
            "--directory",
            str(self.path),
        ]
        logger.info(f"Extracting venv archive: {archive_path}")
        exit_code = subprocess_rt.run(cmd, printer=logger.info)

        if exit_code != 0:
            raise VirtualEnvironmentError(
                f"Failed to extract venv archive: {exit_code}"
            )

        self.__upgrade_scripts_shebang()

    def __upgrade_scripts_shebang(self) -> None:
        with open(self.path / "venv.json", "r", encoding="utf-8") as f:
            venv_config = json.load(f)

        bin_path = self.path / "bin"
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
            logger.info(f"Upgrading shebang for script: {file}")
            if venv_config["base_path"] in content:
                file.write_text(
                    content.replace(venv_config["base_path"], str(self.path)),
                    encoding="utf-8",
                )
