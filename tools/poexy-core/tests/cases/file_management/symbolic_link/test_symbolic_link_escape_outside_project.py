"""
Test case: Symbolic link pointing outside the project

This test verifies that poexy-core prevents unsafe traversal when a symbolic link
in the source directory points to a target outside the project root.

Test scenario:
- A symlink exists in the source directory pointing outside the project
- The build system encounters this symlink during file discovery

Expected behavior:
- The symlink is not followed if it escapes the project root
- The system rejects, sanitizes, or otherwise safely handles the symlink
- Package integrity and security boundaries are maintained

Edge case significance:
Prevents path traversal and supply-chain risks caused by external symlink targets.
"""

import pytest

from poexy_core.utils.symbolic_link import SymlinkEscapingError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkEscapePath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_escape_outside_project"
    )


@pytest.mark.file_operation(
    path=SymlinkEscapePath(
        "src/symlink", "../../../core_functionality/library/src/__init__.py"
    )
)
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkEscapingError,
            match="escaped base path",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(
    path=SymlinkEscapePath(
        "src/symlink", "../../../core_functionality/library/src/__init__.py"
    )
)
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkEscapingError,
            match="escaped base path",
        ):
            assert_sdist_build(project_path)
