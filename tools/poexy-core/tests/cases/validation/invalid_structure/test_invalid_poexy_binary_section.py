"""
Test case: Invalid [tool.poexy.binary] section structure in pyproject.toml
configuration

This test verifies that poexy-core properly handles and reports errors when the
[tool.poexy.binary] section exists but is invalid or empty in the pyproject.toml
configuration. The binary section must be present and correctly structured for
projects that intend to package binaries.

Test scenario:
- A pyproject.toml file contains an empty or invalid [tool.poexy.binary] section
- The build system attempts to process the project configuration
- An appropriate error should be raised indicating the invalid or missing binary
  section content
- The build process should fail before attempting package creation

Expected behavior:
- A PyProjectError or validation error is raised early in the process
- The error message clearly indicates that the [tool.poexy.binary] section is
  invalid or missing required fields
- No build artifacts are created when the binary section is invalid
- Both wheel and sdist builds fail consistently with the same error

Edge case significance:
This tests validation of required configuration sections and their structure. The
binary section is essential for packaging projects with binaries. Proper
validation ensures that projects cannot be built without the necessary and
correctly structured binary configuration.
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
    return sample_project(
        SamplePaths.ValidationInvalidStructure / "invalid_poexy_binary_section"
    )


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
