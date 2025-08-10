"""
Test case: Two-node cycle symbolic link (a -> b -> a)

This test verifies that poexy-core safely handles a 2-node cycle formed by
two symlinks pointing to each other.

Test scenario:
- The source directory contains symlinks `a` and `b` with targets a -> b and b -> a

Expected behavior:
- The system detects the 2-node cycle during resolution without infinite recursion
- A `SymlinkTwoNodeCycleError` is raised, and the cycle is reported clearly
- The build process does not hang and remains robust

Edge case significance:
Prevents denial-of-service and traversal loops caused by mutually-referential
symbolic links.
"""

import re

import pytest

from poexy_core.utils.symbolic_link import SymlinkTwoNodeCycleError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkTwoNodeCyclePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_two_node_cycle"
    )


@pytest.mark.file_operation(path=SymlinkTwoNodeCyclePath("src/symlink"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkTwoNodeCycleError,
            match=re.escape("2-node cycle (length=2)"),
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkTwoNodeCyclePath("src/symlink"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkTwoNodeCycleError,
            match=re.escape("2-node cycle (length=2)"),
        ):
            assert_sdist_build(project_path)
