"""
Test case: Self-loop symbolic link (length-1 cycle)

This test verifies that poexy-core correctly detects a symbolic link that
points to itself.

Test scenario:
- The source directory contains a symlink `a` whose target is itself (a -> a)

Expected behavior:
- The cycle is detected during resolution without infinite recursion or hangs
- A `SymlinkSelfLoopError` is raised with a chain that starts and ends at `a`
- Package integrity and traversal remain stable

Edge case significance:
Protects against malformed self-referential symlinks that could cause hangs
or denial-of-service during file discovery.
"""

import re

import pytest

from poexy_core.utils.symbolic_link import SymlinkSelfLoopError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkSelfLoopPath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_self_loop"
    )


@pytest.mark.file_operation(path=SymlinkSelfLoopPath("src/symlink"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkSelfLoopError,
            match=re.escape("self-loop (length=1)"),
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkSelfLoopPath("src/symlink"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkSelfLoopError,
            match=re.escape("self-loop (length=1)"),
        ):
            assert_sdist_build(project_path)
