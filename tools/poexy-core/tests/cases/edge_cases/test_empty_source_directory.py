"""
Test case: Empty source directory with no files

This test verifies that poexy-core correctly handles the edge case where the
specified source directory exists but contains no files. This tests behavior
when there is literally nothing to package from the source location.

Test scenario:
- A project has a valid source directory path in configuration
- The source directory exists but is completely empty (no files or subdirectories)
- The build system attempts to create packages from the empty source
- Appropriate behavior should occur (error or empty package creation)

Expected behavior:
- The build system detects the empty source directory condition
- Either a meaningful error is raised or an empty package is created
- If empty packages are allowed, they should be valid but contain minimal content
- Consistent behavior across wheel and sdist formats

Edge case significance:
This tests handling of minimal package content scenarios. Empty packages
can occur during development, build errors, or when all content is excluded.
Proper handling ensures predictable behavior and prevents invalid packages
from being created when no content is available.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths
from tests.utils.paths import EmptyDirectoryPath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.EdgeCases / "empty_source_directory")


@pytest.mark.file_operation(path=EmptyDirectoryPath("src"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="Source path is empty",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=EmptyDirectoryPath("src"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="Source path is empty",
        ):
            assert_sdist_build(project_path)
