"""
Test case: File with insufficient read permissions during build

This test verifies that poexy-core properly handles and reports errors when
files in the project have insufficient permissions for reading during the
build process. This tests permission-based access failures.

Test scenario:
- A project contains files with restricted read permissions (chmod 000)
- The build system attempts to read these files for inclusion in packages
- An appropriate error should be raised about permission issues
- The build process should fail gracefully with clear permission error messages

Expected behavior:
- A PermissionError is raised when files cannot be read due to permissions
- The error message identifies the specific file with permission issues
- The error includes information about required permissions
- Permission validation occurs during file processing

Edge case significance:
This tests file system permission handling during builds. Permission issues
can occur in various environments, especially in containerized builds or
when files are created by different users. Proper error handling helps
developers identify and resolve permission-related build failures.
"""

import pytest

from poexy_core.packages.files.resolvers.exceptions import InaccessiblePathError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import InaccessiblePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.EdgeCases / "inaccessible_file")


@pytest.mark.file_operation(path=InaccessiblePath("src/__init__.py"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            InaccessiblePathError,
            match="cannot be read: insufficient permissions",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=InaccessiblePath("src/__init__.py"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            InaccessiblePathError,
            match="cannot be read: insufficient permissions",
        ):
            assert_sdist_build(project_path)
