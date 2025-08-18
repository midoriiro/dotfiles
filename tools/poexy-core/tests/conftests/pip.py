import shutil
from pathlib import Path
from typing import Callable

import pytest
from assertpy import assert_that
from filelock import FileLock

from poexy_core import api
from poexy_core.utils.pip.managers import (
    PackageInstallerProgram,
    PipWheelOptions,
    UvInstallOptions,
    UvOptions,
)
from tests.cases.core_functionality import test_build_self
from tests.utils.markers import MarkerFile
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="session")
def venv_self_build_usage(request, venv_usage_lock_path):
    prevent_venv_self_build = False
    prevent_venv_use = False
    lock_path = venv_usage_lock_path / ".lock"
    lock = FileLock(lock_path)

    with lock:
        marker_file = MarkerFile(venv_usage_lock_path / ".collected")

        if not marker_file.exists():
            session: pytest.Session = request.node
            modules = [item.module.__name__ for item in session.items]
            self_build_module = test_build_self.__name__.rsplit(".", 1)[-1]
            if all(self_build_module == module for module in modules):
                prevent_venv_self_build = True
            else:
                prevent_venv_self_build_item_count = 0
                prevent_venv_use_item_count = 0
                for item in session.items:
                    for marker in item.own_markers:
                        if marker.name == "prevent_venv_self_build":
                            prevent_venv_self_build = True
                            prevent_venv_self_build_item_count += 1
                        if marker.name == "prevent_venv_use":
                            prevent_venv_use = True
                            prevent_venv_use_item_count += 1
                if len(session.items) != prevent_venv_self_build_item_count:
                    prevent_venv_self_build = False
                if len(session.items) != prevent_venv_use_item_count:
                    prevent_venv_use = False
            usage = {
                "prevent_venv_self_build": prevent_venv_self_build,
                "prevent_venv_use": prevent_venv_use,
            }
            marker_file.extra = usage
        else:
            usage = marker_file.read()

        marker_file.touch()

    return usage


@pytest.fixture()
def venv(
    virtualenv_path, create_venv_archive, log_info_section
) -> TestVirtualEnvironment:
    log_info_section("Extracting virtualenv archive")
    venv = TestVirtualEnvironment.create_from_archive(
        create_venv_archive, virtualenv_path
    )
    yield venv
    log_info_section("Removing virtualenv")
    shutil.rmtree(venv.path)


@pytest.fixture()
def pip(venv, log_info_section) -> PackageInstallerProgram:
    log_info_section("Checking poexy-core is installed")
    pip = venv.pip
    assert_that(pip.show("poexy-core", UvOptions.defaults())).is_equal_to(0)
    return pip


@pytest.fixture(scope="session")
def create_venv_archive(
    venv_self_build_usage,
    global_virtualenv_path,
    global_virtualenv_archive_path,
    global_virtualenv_lock_path,
    self_project,
    log_info_section,
) -> Path:
    if venv_self_build_usage["prevent_venv_use"]:
        yield None
        return

    lock_path = global_virtualenv_lock_path / ".lock"
    lock = FileLock(lock_path)

    archive_path = (
        global_virtualenv_archive_path / TestVirtualEnvironment.archive_name()
    )

    with lock:
        marker_file = MarkerFile(global_virtualenv_archive_path / ".archive_created")

        if not marker_file.exists():
            log_info_section("Removing global virtualenv folder and archive")
            shutil.rmtree(global_virtualenv_path, ignore_errors=True)
            shutil.rmtree(global_virtualenv_archive_path, ignore_errors=True)

            log_info_section("Creating global virtualenv folder and archive")
            global_virtualenv_path.mkdir(parents=True, exist_ok=True)
            global_virtualenv_archive_path.mkdir(parents=True, exist_ok=True)

            log_info_section("Creating global virtualenv")
            venv = TestVirtualEnvironment.create_from_path(global_virtualenv_path)

            if not venv_self_build_usage["prevent_venv_self_build"]:
                log_info_section("Building poexy-core")
                self_archive_path = venv.build(self_project)

                log_info_section("Installing poexy-core")
                default_install_options = UvInstallOptions.defaults()
                install_options = UvInstallOptions()
                install_options.no_build_isolation(True)
                install_options = default_install_options + install_options.build()
                venv.pip.install([str(self_archive_path)], install_options)
            else:
                log_info_section("Install poexy-core dependencies")
                requires = api.get_requires_for_build_wheel()
                install_options = UvInstallOptions()
                install_options.no_build_isolation(True)
                venv.pip.install(requires, install_options)

            log_info_section("Creating virtualenv archive")
            archive_path = venv.create_archive(global_virtualenv_archive_path)

            assert_that(str(archive_path)).is_file()

        marker_file.touch()

    try:
        yield archive_path
    finally:
        if marker_file.untouch():
            log_info_section("Removing global virtualenv folder and archive")
            shutil.rmtree(global_virtualenv_archive_path, ignore_errors=True)
            shutil.rmtree(global_virtualenv_path, ignore_errors=True)


@pytest.fixture()
def assert_pip_wheel(
    build_path, pip: PackageInstallerProgram, dist_package_name, log_info_section
) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        log_info_section("Running pip wheel")
        wheel_path = Path(build_path) / "wheel"
        no_build_isolation = True
        check_build_dependencies = True
        options = PipWheelOptions()
        options.no_build_isolation(no_build_isolation)
        options.check_build_dependencies(check_build_dependencies)
        options.wheel_dir(wheel_path)
        returncode = pip.wheel([str(archive_path)], options)
        assert_that(returncode).is_equal_to(0)
        for file in wheel_path.iterdir():
            if file.is_file() and file.name.startswith(dist_package_name()):
                return file
        raise AssertionError(f"Wheel file {dist_package_name()} not found")

    return _assert


@pytest.fixture()
def assert_pip_install(
    pip: PackageInstallerProgram, dist_package_name, log_info_section
) -> Callable[[Path], Path]:
    def _assert(archive_path: Path):
        log_info_section("Running pip install")
        if dist_package_name() == "poexy_core":
            no_build_isolation = False
        else:
            no_build_isolation = True
        options = UvInstallOptions()
        options.verbose(False)
        options.no_build_isolation(no_build_isolation)
        returncode = pip.install([str(archive_path)], options)
        assert_that(returncode).is_equal_to(0)

    return _assert
