"""
Test case: Editable installation mode for development workflows

This test verifies that poexy-core correctly handles editable installation mode
where packages are linked rather than copied to site-packages. Editable installs
use .pth files to enable in-place development without reinstallation.

Test scenario:
- A project is built in editable mode using the editable=True option
- The build system creates a .pth file instead of copying package files
- No actual package files should be installed in site-packages
- No binary executables should be created for editable source packages

Expected behavior:
- A .pth file is created with the package name for path linking
- No package files are copied to site-packages directory
- No binary executables are installed during editable installation
- Editable mode works consistently across wheel and sdist formats

Edge case significance:
This tests editable installation which is crucial for development workflows.
Editable installs allow developers to modify code without reinstalling packages,
significantly improving development iteration speed and debugging capabilities.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.CoreFunctionality / "editable")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path, editable=True)
        assert_zip_file(
            [Path(dist_package_name() + ".pth")],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_false()
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
                Path("editable") / "__init__.py",
            ],
            strict=True,
        )
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
