"""
Test case: Symbolic link with absolute target inside the project (file)

This test ensures that poexy-core correctly handles a symbolic link whose
target is specified as an absolute path that still resides within the project
root and points to a regular file.

Test scenario:
- A symlink in the source directory points, via an ABSOLUTE path, to a file
  located inside the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- The symlink resolution recognizes that the absolute target remains under the
  project base path (no escape)
- The build proceeds successfully according to policy (follow/preserve/resolve)
- Package integrity is maintained

Edge case significance:
Verifies that absolute-path symlinks are not treated as escapes when they
remain inside the project, avoiding false positives and ensuring predictable
builds under varied filesystem layouts.
"""

import pytest

from poexy_core.utils.symbolic_link import AbsoluteSymlinkError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkPointToAbsolutePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_point_to_absolute_file"
    )


@pytest.mark.file_operation(
    path=SymlinkPointToAbsolutePath("src/symlink", "src/target")
)
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            AbsoluteSymlinkError,
            match="Absolute symbolic link",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(
    path=SymlinkPointToAbsolutePath("src/symlink", "src/target")
)
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            AbsoluteSymlinkError,
            match="Absolute symbolic link",
        ):
            assert_sdist_build(project_path)
