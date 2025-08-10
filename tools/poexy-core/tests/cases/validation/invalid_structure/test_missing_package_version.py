"""
Test case: Missing package version in pyproject.toml configuration

This test verifies that poexy-core properly handles and reports errors when the
package version is missing or undefined in the [project] section of pyproject.toml.
The package version is a required field for all package types.

Test scenario:
- A pyproject.toml file is missing the 'version' field in [project] section
- The build system attempts to determine the package version
- An appropriate error should be raised indicating the missing requirement
- The build process should fail before attempting package creation

Expected behavior:
- A ValueError or validation error is raised early in the process
- The error message clearly indicates that package version is required
- No build artifacts are created when the version is missing
- Both wheel and sdist builds fail consistently with the same error

Edge case significance:
This tests validation of required metadata fields. Package version is fundamental
to Python packaging and must be present for distribution. Proper validation
ensures packages cannot be created without essential versioning information.
"""

import re

import pytest

from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.ValidationInvalidStructure / "missing_package_version"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[project] section must contain a version"),
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[project] section must contain a version"),
        ):
            assert_sdist_build(project_path)
