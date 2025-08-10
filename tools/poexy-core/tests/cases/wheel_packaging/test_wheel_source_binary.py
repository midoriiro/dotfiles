"""
Test case: Wheel packaging with combined source and binary formats

This test verifies that poexy-core correctly creates wheel packages containing
both Python source code and binary executables. This tests hybrid packaging
where a project provides both importable modules and command-line tools.

Test scenario:
- A project is configured for both source and binary format packaging
- The project contains Python source code and binary entry points
- The build system creates both wheel and sdist packages with dual formats
- The resulting package should contain both Python modules and executables

Expected behavior:
- Python source files are included in the wheel package
- Binary executables are created and included in the wheel package
- Source files are installed in site-packages during installation
- Binary executables are installed in bin directory during installation

Edge case significance:
This tests hybrid packaging which is important for projects that serve as both
libraries and command-line tools. Combined packaging provides maximum utility
by offering both programmatic access and direct executable functionality.
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
    return sample_project(SamplePaths.WheelPackaging / "wheel_source_binary")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    wheel_data_scripts_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(
            project_path, _format={WheelFormat.Source, WheelFormat.Binary}
        )
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
                wheel_data_scripts_folder(default_python_tag) / package_name(),
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
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
        assert_tar_file = assert_sdist_build(
            project_path, _format={WheelFormat.Source, WheelFormat.Binary}
        )
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_true()
