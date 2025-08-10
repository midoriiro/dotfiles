"""
Test case: Binary dependency resolution from VCS sources

This test verifies that poexy-core correctly handles binary packaging when
dependencies are sourced from version control systems (VCS). VCS dependencies
must be properly resolved and integrated into binary executables.

Test scenario:
- A binary project specifies dependencies from VCS sources (e.g., Git repositories)
- The build system resolves VCS dependencies during binary packaging
- The resulting binary executable should include the VCS dependency
- Binary execution should work correctly with the integrated VCS dependency

Expected behavior:
- VCS dependencies are properly resolved and included in binary packages
- Binary executables function correctly with integrated VCS dependencies
- VCS dependency resolution works consistently across wheel and sdist formats
- Binary execution produces expected output with VCS dependency functionality

Edge case significance:
This tests VCS dependency integration in binary packaging which is important
for projects that depend on development versions or private repositories.
Proper VCS handling ensures that binary distributions include all necessary code.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.packages.format import WheelFormat
from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.Dependencies / "binary_dependency_vcs")


@pytest.mark.use_git_server()
def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_scripts_folder,
    current_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
    execute_binary,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path, _format={WheelFormat.Binary})
        assert_zip_file(
            [
                wheel_data_scripts_folder(current_python_tag) / package_name(),
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_false()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_true()
        result = execute_binary(binary_path)
        if result.returncode != 0:
            raise AssertionError(f"Binary failed to execute: {result.stderr}")
        assert_that(result.stdout).is_equal_to("Hello, World!\n")


@pytest.mark.use_git_server()
def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
    execute_binary,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path, _format={WheelFormat.Binary})
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_false()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_true()
        result = execute_binary(binary_path)
        if result.returncode != 0:
            raise AssertionError(f"Binary failed to execute: {result.stderr}")
        assert_that(result.stdout).is_equal_to("Hello, World!\n")
