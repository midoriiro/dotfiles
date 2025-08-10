"""
Test case: Conflicting local dependency specifications

This test verifies that poexy-core correctly detects and reports errors when
local dependencies have conflicting or ambiguous specifications. Conflicting
dependencies can cause build failures and must be properly validated.

Test scenario:
- A project specifies local dependencies with conflicting configuration
- Dependencies point to directories instead of proper package references
- The build system attempts to resolve the conflicting dependency specifications
- Appropriate validation errors should be raised for conflicting dependencies

Expected behavior:
- Conflicting local dependencies are detected during validation
- Error messages clearly identify the problematic dependency configuration
- Build fails early with guidance on resolving dependency conflicts
- Conflict detection is consistent across wheel and sdist formats

Edge case significance:
This tests dependency validation which is essential for preventing build
failures and configuration errors. Proper conflict detection helps users
identify and resolve dependency specification issues early in the build process.
"""

import pytest

from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.Dependencies / "dependency_conflicting_local")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing to a directory",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing to a directory",
        ):
            assert_sdist_build(project_path)
