"""
Test case: Wheel packaging with source format only

This test verifies that poexy-core correctly creates wheel packages containing
only Python source code without any binary components. This tests the standard
Python library packaging workflow for pure Python packages.

Test scenario:
- A project is configured for source format packaging only
- The project contains Python source code but no binary entry points
- The build system creates both wheel and sdist packages
- The resulting package should contain only Python modules

Expected behavior:
- Python source files are included in the wheel package
- Source files are installed in site-packages during installation
- No binary executables are created or installed
- Both wheel and sdist formats handle source-only packaging correctly

Edge case significance:
This tests pure Python packaging which is the most common packaging scenario.
Source-only wheels ensure maximum compatibility across Python installations
and platforms while maintaining the simplicity of traditional Python modules.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.WheelPackaging / "wheel_source")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py"
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
