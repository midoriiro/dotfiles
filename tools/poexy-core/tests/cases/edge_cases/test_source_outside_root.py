"""
Test case: Source directory located outside project root

This test verifies that poexy-core correctly handles the case where the source
directory is specified as a path outside the project root directory. This
tests path resolution and security boundaries for external source locations.

Test scenario:
- A pyproject.toml specifies a source path that points outside the project root
- The external source directory contains valid Python files
- The build system attempts to include files from the external location
- Security and path validation should prevent or control external access

Expected behavior:
- External source paths are either rejected with security errors
- Or external sources are handled with appropriate validation and warnings
- Path traversal attacks are prevented through proper validation
- Clear error messages explain any restrictions on external sources

Edge case significance:
This tests security boundaries and path validation for source directories.
External sources can create security vulnerabilities and make packages
non-reproducible. Proper handling ensures package builds are secure and
contained within expected boundaries while providing clear feedback.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.EdgeCases / "source_outside_root")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="Source path is outside the root project directory",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="Source path is outside the root project directory",
        ):
            assert_sdist_build(project_path)
