"""
Test case: Symbolic link chain exceeds maximum resolution steps

This test verifies that poexy-core aborts resolution when encountering an
excessively long symlink chain that does not resolve to a regular file and
does not repeat within the configured step limit.

Test scenario:
- The source directory contains a linear chain of symlinks longer than the
  configured `max_steps` (e.g., > 1000), each pointing to a unique next link

Expected behavior:
- Resolution is stopped after the maximum number of steps is reached
- A `SymlinkMaxStepReachedError` is raised with the observed chain
- The system avoids unbounded processing time and remains responsive

Edge case significance:
Protects against denial-of-service via pathologically long symlink chains
that never terminate within a reasonable bound.
"""

import pytest

from poexy_core.utils.symbolic_link import SymlinkMaxStepReachedError
from tests.conftests.paths import SamplePaths
from tests.utils.paths import SymlinkMaxStepReachedPath

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_max_step_reached"
    )


@pytest.mark.file_operation(path=SymlinkMaxStepReachedPath("src/symlink"))
def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            SymlinkMaxStepReachedError,
            match="cannot be resolved and has reached maximum steps",
        ):
            assert_wheel_build(project_path)


@pytest.mark.file_operation(path=SymlinkMaxStepReachedPath("src/symlink"))
def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            SymlinkMaxStepReachedError,
            match="cannot be resolved and has reached maximum steps",
        ):
            assert_sdist_build(project_path)
