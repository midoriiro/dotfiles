"""
Test case: Glob absolute symlink resolution (file target)

This test verifies that poexy-core correctly rejects absolute symbolic links
during glob pattern matching, even when the target is a file within
the project boundaries.

Test scenario:
- A glob pattern matches an entry that is an absolute symlink to an in-project
  file
- The symlink uses an absolute path target (which is not permitted)

Expected behavior:
- The absolute symlink is detected and rejected with AbsoluteSymlinkError
- Build process fails with appropriate error message
- Security policy against absolute symlinks is enforced consistently

Edge case significance:
Ensures that absolute symlinks are always rejected regardless of whether
they target files or directories, maintaining consistent security boundaries
in the packaging system.
"""

import pytest

from poexy_core.utils.symbolic_link import AbsoluteSymlinkError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkPointToAbsolutePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_glob_absolute_file_target"
    )


@pytest.mark.file_operation(path=SymlinkPointToAbsolutePath("symlink", "target"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            AbsoluteSymlinkError,
            match="Absolute symbolic link",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkPointToAbsolutePath("symlink", "target"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            AbsoluteSymlinkError,
            match="Absolute symbolic link",
        ):
            assert_sdist_build(project_path)
