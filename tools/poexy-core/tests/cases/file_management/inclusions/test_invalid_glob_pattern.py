"""
Test case: Invalid glob pattern in includes or excludes configuration

This test verifies that poexy-core properly handles and reports errors when
invalid glob patterns are specified in includes or excludes sections. Glob
patterns must follow proper syntax and cannot contain invalid characters.

Test scenario:
- A pyproject.toml file contains malformed glob patterns in includes/excludes
- The pattern validation attempts to parse the glob expressions
- An appropriate error should be raised indicating the syntax issue
- The build process should fail before file matching attempts

Expected behavior:
- A ValueError is raised during glob pattern validation
- The error message identifies the specific invalid pattern
- Proper glob syntax examples may be provided in the error message
- Pattern validation occurs early in the configuration parsing phase

Edge case significance:
This tests pattern validation for file inclusion/exclusion rules. Invalid
glob patterns can cause unexpected build behavior or file matching failures.
Proper validation ensures that file selection rules are syntactically correct
and will function as intended during the build process.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "invalid_glob_pattern")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="contains invalid characters",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="contains invalid characters",
        ):
            assert_sdist_build(project_path)
