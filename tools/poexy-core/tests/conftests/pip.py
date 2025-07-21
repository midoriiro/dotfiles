import zipfile
from pathlib import Path
from typing import Callable

import pytest
from assertpy import assert_that

from poexy_core import api
from tests.pip import Pip

# pylint: disable=redefined-outer-name


@pytest.fixture()
def pip(
    virtualenv_path, create_venv_archive, log_info_section, pyinstaller_path
) -> Pip:
    pyinstaller_path()
    log_info_section("Creating virtualenv")
    pip = Pip(virtualenv_path)
    pip.extract_virtualenv_archive(create_venv_archive)
    log_info_section("Checking poexy-core is installed")
    assert_that(pip.show("poexy-core")).is_equal_to(0)
    return pip


@pytest.fixture(scope="session")
def create_venv_archive(
    global_virtualenv_path, global_virtualenv_archive_path, self_build, log_info_section
) -> Path:
    pip = Pip(global_virtualenv_path)
    log_info_section("Creating virtualenv")
    pip.create_virtualenv()
    log_info_section("Installing poexy-core")
    pip.install(self_build)
    log_info_section("Creating virtualenv archive")
    archive_path = pip.create_virtualenv_archive(global_virtualenv_archive_path)
    assert_that(str(archive_path)).is_file()
    return archive_path


@pytest.fixture(scope="session")
def self_build(project, self_project, self_project_dist_path, log_info_section):
    with project(self_project):
        log_info_section("Building self project")
        filename = api.build_wheel(str(self_project_dist_path))
        archive_path = self_project_dist_path / filename
        assert_that(str(archive_path)).is_file()
        assert_that(zipfile.is_zipfile(archive_path)).is_true()
        return archive_path


@pytest.fixture()
def assert_pip_wheel(
    build_path, pip, dist_package_name, log_info_section
) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        log_info_section("Running pip wheel")
        wheel_path = Path(build_path) / "wheel"
        if dist_package_name() == "poexy_core":
            no_build_isolation = False
            check_build_dependencies = True
        else:
            no_build_isolation = True
            check_build_dependencies = True
        returncode = pip.wheel(
            archive_path, wheel_path, no_build_isolation, check_build_dependencies
        )
        assert_that(returncode).is_equal_to(0)
        for file in wheel_path.iterdir():
            if file.is_file() and file.name.startswith(dist_package_name()):
                return file
        raise AssertionError(f"Wheel file {dist_package_name()} not found")

    return _assert


@pytest.fixture()
def assert_pip_install(
    install_path, pip, dist_package_name, log_info_section
) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        log_info_section("Running pip install")
        if dist_package_name() == "poexy_core":
            no_build_isolation = False
            check_build_dependencies = True
        else:
            no_build_isolation = True
            check_build_dependencies = True
        returncode = pip.install(
            archive_path, install_path, no_build_isolation, check_build_dependencies
        )
        assert_that(returncode).is_equal_to(0)
        return install_path

    return _assert
