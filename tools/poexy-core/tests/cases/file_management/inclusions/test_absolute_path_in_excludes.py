"""
Test case: Absolute path specified in excludes configuration

This test verifies that poexy-core properly handles and reports errors when
absolute paths are used in excludes sections. All paths in excludes should
be relative to the project root for portability and security.

Test scenario:
- A pyproject.toml file contains absolute paths in excludes configuration
- The path validation checks for absolute path usage
- An appropriate error should be raised requiring relative paths
- The build process should fail to prevent security and portability issues

Expected behavior:
- A ValueError is raised when absolute paths are detected
- The error message explains why relative paths are required
- The specific absolute path is identified in the error message
- Path validation occurs during configuration parsing

Edge case significance:
This tests security and portability validation for file paths. Absolute paths
can create security vulnerabilities and make packages non-portable across
different systems. Proper validation ensures packages work consistently
across different environments and installation locations.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "absolute_path_in_excludes"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="should be relative",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="should be relative",
        ):
            assert_sdist_build(project_path)
