"""
Test case: Binary package with custom binary name configuration

This test verifies that poexy-core correctly handles binary packaging when a
custom binary name is specified in the project configuration. This tests the
ability to control the final executable name independently from the package name.

Test scenario:
- A project specifies a custom binary name in the configuration
- The project is configured for binary format packaging
- The build system creates both wheel and sdist packages
- The resulting binary should use the specified custom name

Expected behavior:
- The binary executable is created with the specified custom name
- The binary is included in the wheel package with the correct name
- The binary is installed in the correct bin directory during installation
- No Python package files are installed in site-packages for binary-only format

Edge case significance:
This tests custom binary naming which is important for user experience and
compatibility. Custom names allow projects to have user-friendly executable
names that may differ from the Python package name for better CLI usability.
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
    return sample_project(SamplePaths.BinaryPackaging / "binary_name")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_scripts_folder,
    current_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
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


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
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
