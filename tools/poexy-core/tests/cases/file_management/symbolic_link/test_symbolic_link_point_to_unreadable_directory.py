"""
Test case: Symbolic link pointing to an unreadable directory

This test verifies that poexy-core correctly handles a symbolic link whose
resolved target is a directory without sufficient read permissions.

Test scenario:
- A symlink exists in the source directory pointing (directly or via a chain)
  to a directory with no readable bits set
- The build system encounters this symlink during file discovery

Expected behavior:
- The system raises `SymlinkNotAccessibleError` when the target directory
  cannot be read due to insufficient permissions
- Package integrity and security boundaries are preserved without leaking
  restricted contents

Edge case significance:
Complements the unreadable-file test by covering unreadable directories,
ensuring consistent permission enforcement for both target types.
"""

import pytest

from poexy_core.utils.symbolic_link import SymlinkNotAccessibleError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkPointToUnreadablePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_point_to_unreadable_directory"
    )


@pytest.mark.file_operation(path=SymlinkPointToUnreadablePath("symlink", "unreadable"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkNotAccessibleError,
            match="insufficient permissions or file does not exist",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkPointToUnreadablePath("symlink", "unreadable"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkNotAccessibleError,
            match="insufficient permissions or file does not exist",
        ):
            assert_sdist_build(project_path)
