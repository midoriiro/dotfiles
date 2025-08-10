"""
Test case: Broken symbolic link

This test verifies that poexy-core handles a broken symbolic link (a symlink
whose target does not exist) in the source directory without failing the build
unexpectedly.

Test scenario:
- The source directory contains a symlink whose target path is missing or has
  been removed
- The build system encounters this symlink during file discovery

Expected behavior:
- The broken symlink is detected and handled gracefully
- The system reports, skips, or otherwise safely manages the link according to
  policy without crashing
- Package integrity is preserved and no infinite retries or hangs occur

Edge case significance:
Broken symlinks commonly appear during refactors or partial checkouts; robust
handling prevents flaky builds and improves developer experience.
"""

import pytest

from poexy_core.utils.symbolic_link import BrokenSymlinkError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import BrokenSymlinkPath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_broken"
    )


@pytest.mark.file_operation(path=BrokenSymlinkPath("src/symlink", "src/symlink-target"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            BrokenSymlinkError,
            match="Broken symbolic link",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=BrokenSymlinkPath("src/symlink", "src/symlink-target"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            BrokenSymlinkError,
            match="Broken symbolic link",
        ):
            assert_sdist_build(project_path)
