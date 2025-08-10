"""
Test case: Missing README file specified in project metadata

This test verifies that poexy-core properly handles and reports errors when a
README file is specified in the project metadata but the file does not exist
on the filesystem. README files provide important project documentation.

Test scenario:
- A pyproject.toml file specifies a readme file in project metadata
- The specified README file does not exist at the given location
- The build system attempts to include the README in package metadata
- An appropriate error should be raised about the missing README file

Expected behavior:
- A FileNotFoundError is raised when the README file cannot be found
- The error message clearly identifies the missing README file path
- The error occurs during metadata processing phase
- README validation prevents incomplete package metadata

Edge case significance:
This tests README file validation which affects package presentation on
PyPI and other repositories. Missing README files result in packages
without proper documentation, making them less useful to potential users.
Proper validation ensures documentation is included in distributions.
"""

import pytest
from pydantic import ValidationError

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.ValidationMissingFiles / "missing_readme_file")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="file path 'README.md' does not exist",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValidationError,
            match="file path 'README.md' does not exist",
        ):
            assert_sdist_build(project_path)
