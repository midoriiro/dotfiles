"""
Test case: Conflicting local dependencies in hybrid format projects

This test verifies that poexy-core correctly detects and reports errors when
local dependencies have conflicting specifications in projects configured for
hybrid source and binary formats. Conflicts must be detected across all formats.

Test scenario:
- A project is configured for both source and binary formats
- Local dependencies have conflicting or invalid directory specifications
- The build system attempts to resolve dependencies for hybrid packaging
- Validation errors should be raised consistently across both formats

Expected behavior:
- Conflicting dependencies are detected for both source and binary formats
- Error messages identify the problematic dependency and affected formats
- Build fails early regardless of which format combination is used
- Conflict detection works consistently across hybrid format configurations

Edge case significance:
This tests dependency validation in hybrid format scenarios which is important
for complex projects that generate multiple package types. Consistent validation
ensures that dependency issues are caught regardless of format configuration.
"""

import pytest

from poexy_core.packages.format import WheelFormat
from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.Dependencies / "dependency_conflicting_local_hybrid"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing to a directory",
        ):
            assert_wheel_build(
                project_path, _format={WheelFormat.Source, WheelFormat.Binary}
            )


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing to a directory",
        ):
            assert_sdist_build(
                project_path, _format={WheelFormat.Source, WheelFormat.Binary}
            )
