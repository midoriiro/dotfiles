"""
Test case: Symbolic link pointing to an unreadable file

This test verifies that poexy-core correctly handles a symbolic link whose
final resolved target is a regular file without sufficient read permissions.

Test scenario:
- A symlink exists in the source directory pointing (directly or via a chain)
  to a regular file with no readable bits set
- The build system encounters this symlink during file discovery

Expected behavior:
- The system raises `SymlinkNotAccessibleError` when the target cannot be read
  due to insufficient permissions
- Package integrity and security boundaries are maintained without leaking
  restricted contents

Edge case significance:
Prevents accidental inclusion or processing of files that should not be
accessible, ensuring secure and deterministic builds.
"""

import pytest

from poexy_core.utils.symbolic_link import SymlinkNotAccessibleError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkPointsToUnreadableFilePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_points_to_unreadable_file"
    )


@pytest.mark.file_operation(
    path=SymlinkPointsToUnreadableFilePath("src/symlink", "src/../unreadable")
)
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkNotAccessibleError,
            match="insufficient permissions or file does not exist",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(
    path=SymlinkPointsToUnreadableFilePath("src/symlink", "src/../unreadable")
)
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkNotAccessibleError,
            match="insufficient permissions or file does not exist",
        ):
            assert_sdist_build(project_path)
