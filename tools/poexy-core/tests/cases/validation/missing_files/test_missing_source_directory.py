"""
Test case: Missing source directory specified in package configuration

This test verifies that poexy-core properly handles and reports errors when the
source directory specified in the package configuration does not exist on the
filesystem. This is different from invalid paths - this tests existing configuration
pointing to non-existent directories.

Test scenario:
- A pyproject.toml file has valid syntax but points to a non-existent source directory
- The build system attempts to access the specified source directory
- An appropriate error should be raised indicating the directory is missing
- The build process should fail gracefully with informative error messages

Expected behavior:
- A FileNotFoundError or similar is raised when accessing the source directory
- The error message clearly identifies which source directory is missing
- The error includes the full path that was attempted to be accessed
- No partial build artifacts are created when source is missing

Edge case significance:
This tests filesystem validation for configured paths. Source directories
can be accidentally deleted, moved, or renamed after configuration. Proper
error handling helps developers quickly identify when their project structure
doesn't match their configuration.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.ValidationMissingFiles / "missing_source_directory"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="'missing_source_directory' does not exist",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="'missing_source_directory' does not exist",
        ):
            assert_sdist_build(project_path)
