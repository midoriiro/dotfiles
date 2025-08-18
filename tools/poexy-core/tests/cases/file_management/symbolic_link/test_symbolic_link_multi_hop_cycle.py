"""
Test case: Multi-node cycle symbolic link (a -> b -> ... -> a)

This test verifies that poexy-core correctly detects cycles involving
three or more symlinks that eventually reference back to the origin.

Test scenario:
- The source directory contains a chain of symlinks a -> b -> c -> ... -> a

Expected behavior:
- The cycle is detected during resolution without infinite recursion or hangs
- A `SymlinkChainCycleError` is raised with information about the chain
- Package integrity is preserved despite the malformed filesystem state

Edge case significance:
Ensures resilience against longer cycles that could otherwise cause traversal
loops or resource exhaustion.
"""

import re

import pytest

from poexy_core.utils.symbolic_link import SymlinkChainCycleError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkMultiNodeCyclePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_multi_hop_cycle"
    )


@pytest.mark.file_operation(path=SymlinkMultiNodeCyclePath("src/symlink"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkChainCycleError,
            match=re.escape("multi-node cycle (length=6)"),
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkMultiNodeCyclePath("src/symlink"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkChainCycleError,
            match=re.escape("multi-node cycle (length=6)"),
        ):
            assert_sdist_build(project_path)
