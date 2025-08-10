"""
Test case: Binary package with minimal configuration and auto-detection

This test verifies that poexy-core correctly handles binary packaging when
minimal configuration is provided and entry points must be auto-detected.
This tests the automatic discovery of entry points for binary generation.

Test scenario:
- A project has minimal binary configuration without explicit entry points
- The build system must auto-detect the appropriate entry point
- The project is configured for binary format packaging
- The build system creates both wheel and sdist packages

Expected behavior:
- The build system successfully auto-detects the entry point
- The binary executable is created and included in the wheel package
- The binary is installed in the correct bin directory during installation
- No Python package files are installed in site-packages for binary-only format

Edge case significance:
This tests auto-detection capabilities which are essential for simplifying
the binary packaging process. Auto-detection reduces configuration overhead
and makes binary packaging accessible for projects with standard structures.
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
    return sample_project(SamplePaths.BinaryPackaging / "binary_without_config")


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
