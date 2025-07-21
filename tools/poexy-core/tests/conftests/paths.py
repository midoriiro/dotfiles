import os
import sys
import uuid
from pathlib import Path

import pytest

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


@pytest.fixture(scope="function")
def install_path(tmp_root):
    return tmp_root / "install"


@pytest.fixture(scope="session")
def global_virtualenv_path(tmpdir_factory) -> Path:
    tmpdir = tmpdir_factory.mktemp("venv")
    return Path(tmpdir)


@pytest.fixture(scope="session")
def global_virtualenv_archive_path(tmpdir_factory) -> Path:
    tmpdir = tmpdir_factory.mktemp("venv-archive")
    return Path(tmpdir)


@pytest.fixture(scope="function")
def virtualenv_path(tmp_root):
    return tmp_root / "venv"


@pytest.fixture(scope="function")
def pyinstaller_path(tmp_root):
    path = tmp_root / "pyinstaller"

    def _pyinstaller_path():
        os.environ["PYINSTALLER_CONFIG_DIR"] = str(path)

    return _pyinstaller_path


@pytest.fixture(scope="function")
def site_packages_path(install_path) -> Path:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    path = install_path / "lib" / f"python{python_version}" / "site-packages"
    return path
