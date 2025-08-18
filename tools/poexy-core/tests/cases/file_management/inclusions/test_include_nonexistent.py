"""
Test case: Include patterns that match no files

This test verifies that poexy-core correctly handles include patterns that do not
match any files in the project. The expected behavior is that the build succeeds
but logs a warning when an include rule is specified but does not match any files,
as this may indicate a misconfiguration or an obsolete pattern.

Test scenario:
- A pyproject.toml file specifies include patterns that match no existing files
- The build system processes these non-matching include patterns
- The build should succeed but log a warning about the non-matching pattern

Expected behavior:
- Non-matching include patterns do not cause the build to fail
- A warning is logged indicating which pattern did not match any files
- This alerts users to potentially obsolete or incorrect include rules
- The build completes successfully despite the non-matching patterns

Edge case significance:
This tests the robustness of pattern matching when include rules become obsolete
or are specified preemptively. Non-matching includes can occur when project
structure changes or when generic include patterns are used. Proper handling
ensures that builds continue to work while providing feedback about potentially
incorrect include rules, balancing strictness with usability.
"""

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "include_nonexistent")


def test_wheel(project, project_path, assert_wheel_build, caplog):
    with project(project_path):
        assert_wheel_build(project_path)
        assert_that(caplog.text).contains(
            "Pattern './**/nonexistent/*' resolved nothing"
        )


def test_sdist(project, project_path, assert_sdist_build, caplog):
    with project(project_path):
        assert_sdist_build(project_path)
        assert_that(caplog.text).contains(
            "Pattern './**/nonexistent/*' resolved nothing"
        )
