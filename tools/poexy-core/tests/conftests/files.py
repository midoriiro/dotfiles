from pathlib import Path
from typing import Callable, Optional

import pytest
from assertpy import assert_that

from poexy_core.packages.package import ModulePackage
from tests.utils.asserts import AssertPathKind, AssertPaths, AssertPathsType
from tests.utils.venv import TestVirtualEnvironment


def _prepare_files(
    files: AssertPaths,
    purelib_path: Path,
    platlib_path: Optional[Path],
    data_platform_data_path: Optional[Path],
    data_platform_config_path: Optional[Path],
    data_platform_cache_path: Optional[Path],
    binary_path: Optional[Path],
    package_name: str,
):
    files.remap_base_path(
        purelib_path,
        AssertPathKind.Purelib,
    )
    if platlib_path:
        files.remap_base_path(
            platlib_path,
            AssertPathKind.Platlib,
        )
    if data_platform_data_path:
        files.remap_base_path(
            data_platform_data_path,
            AssertPathKind.Platform | AssertPathKind.Data,
        )
    if data_platform_config_path:
        files.remap_base_path(
            data_platform_config_path,
            AssertPathKind.Platform | AssertPathKind.Config,
        )
    if data_platform_cache_path:
        files.remap_base_path(
            data_platform_cache_path,
            AssertPathKind.Platform | AssertPathKind.Cache,
        )
    if binary_path:
        files.remap_base_path(
            binary_path,
            AssertPathKind.Binary,
        )
    files.expand(package_name, AssertPathKind.Binary)


@pytest.fixture()
def prepare_venv_files(
    dist_package_name,
    package_name,
    platform_directories,
    venv: TestVirtualEnvironment,
):
    def _prepare(
        expected_files: AssertPathsType,
    ):
        if not isinstance(expected_files, AssertPaths):
            expected_files = AssertPaths(expected_files)

        purelib_path = venv.site_package / dist_package_name()
        platlib_path = venv.site_package / dist_package_name()
        data_platform_data_path = venv.path / platform_directories().data
        data_platform_config_path = venv.path / platform_directories().config
        data_platform_cache_path = venv.path / platform_directories().cache
        binary_path = venv.bin_path

        _prepare_files(
            expected_files,
            purelib_path,
            platlib_path,
            data_platform_data_path,
            data_platform_config_path,
            data_platform_cache_path,
            binary_path,
            package_name(),
        )

    return _prepare


@pytest.fixture()
def prepare_zip_files(
    default_python_tag,
    current_python_tag,
    dist_package_name,
    package_name,
    wheel_dist_info_folder,
    wheel_data_purelib_folder,
    wheel_data_platlib_folder,
    wheel_data_data_folder,
    wheel_data_scripts_folder,
    platform_directories,
    venv: TestVirtualEnvironment,
):
    def _prepare(
        expected_files: AssertPathsType,
    ):
        if not isinstance(expected_files, AssertPaths):
            expected_files = AssertPaths(expected_files)

        venv_site_packages = venv.site_package

        try:
            python_tag = current_python_tag
            dist_info_path = wheel_dist_info_folder(python_tag)
            assert_that(str(venv_site_packages / dist_info_path)).exists()
        except AssertionError:
            python_tag = default_python_tag
            dist_info_path = wheel_dist_info_folder(python_tag)
            assert_that(str(venv_site_packages / dist_info_path)).exists()

        purelib_path = wheel_data_purelib_folder(python_tag) / dist_package_name()
        platlib_path = wheel_data_platlib_folder(python_tag) / dist_package_name()
        data_platform_data_path = (
            wheel_data_data_folder(python_tag) / platform_directories().data
        )
        data_platform_config_path = (
            wheel_data_data_folder(python_tag) / platform_directories().config
        )
        data_platform_cache_path = (
            wheel_data_data_folder(python_tag) / platform_directories().cache
        )
        binary_path = wheel_data_scripts_folder(python_tag)

        _prepare_files(
            expected_files,
            purelib_path,
            platlib_path,
            data_platform_data_path,
            data_platform_config_path,
            data_platform_cache_path,
            binary_path,
            package_name(),
        )

    return _prepare


@pytest.fixture()
def prepare_tar_files(
    package: Callable[[], ModulePackage],
    package_name,
):
    def _prepare(
        expected_files: AssertPathsType,
    ):
        if not isinstance(expected_files, AssertPaths):
            expected_files = AssertPaths(expected_files)

        purelib_path = package().source

        _prepare_files(
            expected_files,
            purelib_path,
            package_name=package_name(),
            platlib_path=None,
            data_platform_data_path=None,
            data_platform_config_path=None,
            data_platform_cache_path=None,
            binary_path=None,
        )

    return _prepare
