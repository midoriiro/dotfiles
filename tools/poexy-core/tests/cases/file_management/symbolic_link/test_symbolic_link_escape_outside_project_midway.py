"""
Test case: Symbolic link with intermediate link escaping outside the project

This test verifies that poexy-core prevents unsafe traversal when a symbolic link
chain contains an intermediate link that points outside the project root, even if
the final target is within the project.

Test scenario:
- A symlink chain exists where an intermediate link escapes the project boundaries
- The build system encounters this symlink during file discovery
- The chain may eventually point back to a valid target within the project

Expected behavior:
- The symlink chain is not followed if any intermediate link escapes the project root
- The system detects and rejects chains with escaping intermediate links
- Package integrity and security boundaries are maintained throughout the entire chain

Edge case significance:
Prevents sophisticated path traversal attacks that use intermediate escaping links
to bypass security checks while appearing to have valid final targets.
"""

import pytest

from poexy_core.utils.symbolic_link import SymlinkEscapingError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkEscapeMidwayPath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_escape_outside_project_midway"
    )


@pytest.mark.file_operation(
    path=SymlinkEscapeMidwayPath("src/symlink", "src/__init__.py")
)
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkEscapingError,
            match="escaped base path",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(
    path=SymlinkEscapeMidwayPath("src/symlink", "src/__init__.py")
)
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkEscapingError,
            match="escaped base path",
        ):
            assert_sdist_build(project_path)
