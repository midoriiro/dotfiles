import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest
from filelock import FileLock

from tests.utils.markers import MarkerFile

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def samples_path():
    return Path(__file__).parent.parent / "samples"


@pytest.fixture(scope="session")
def self_project_dist_path(tmpdir_factory) -> Path:
    tmpdir = tmpdir_factory.mktemp("dist")
    return Path(tmpdir)


@pytest.fixture(scope="function")
def tmp_root(tmpdir_factory):
    path = tmpdir_factory.mktemp(f"test_{uuid.uuid4().hex[:8]}")
    return Path(path)


@pytest.fixture(scope="function")
def dist_path(tmp_root):
    return tmp_root / "dist"


@pytest.fixture(scope="function")
def dist_temp_path(dist_path):
    return dist_path / "temp"


@pytest.fixture(scope="function")
def build_path(tmp_root):
    return tmp_root / "build"


@pytest.fixture(scope="session")
def global_tmp_root(testrun_uid, log_info_section) -> Path:
    base_tmp = Path(tempfile.gettempdir())
    path = base_tmp / "poexy-core-tmp"
    lock_path = str(path) + ".lock"
    lock = FileLock(lock_path)

    with lock:
        init_marker = MarkerFile(path / ".initialized", {"testrun_uid": testrun_uid})

        if not init_marker.exists():
            log_info_section("Removing global tmp root")
            shutil.rmtree(path, ignore_errors=True)
            path.mkdir(parents=True, exist_ok=True)

        init_marker.touch()

    try:
        yield path
    finally:
        if init_marker.untouch():
            log_info_section("Removing global tmp root")
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(scope="session")
def global_virtualenv_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def global_virtualenv_archive_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv-archive"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def global_virtualenv_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "venv-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def http_server_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "http-server"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def git_server_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "git-server"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def server_lock_path(global_tmp_root: Path) -> Path:
    path = global_tmp_root / "server-lock"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="function")
def virtualenv_path(tmp_root):
    return tmp_root / "venv"


@pytest.fixture(scope="function", autouse=True)
def pyinstaller_path(tmp_root):
    path = tmp_root / "pyinstaller"
    os.environ["PYINSTALLER_CONFIG_DIR"] = str(path)
