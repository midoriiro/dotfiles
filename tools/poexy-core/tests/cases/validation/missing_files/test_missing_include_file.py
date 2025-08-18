"""
Test case: Missing file specified in includes configuration

This test verifies that poexy-core properly handles missing files in include
patterns by logging warnings rather than raising errors. This validates the
non-blocking behavior for include pattern resolution.

Test scenario:
- A pyproject.toml file lists specific files in includes section
- One or more of the listed files do not exist on the filesystem
- The build system attempts to include the specified files
- A warning should be logged but the build should continue successfully

Expected behavior:
- No ValidationError is raised when missing include files are detected
- A warning message is logged identifying the unresolved include pattern
- The build continues and completes successfully despite missing included files
- The warning occurs during the file collection phase of the build

Edge case significance:
This tests include pattern tolerance. Missing include files should not break
the build process since include patterns may reference files that are
conditionally present. The system should gracefully handle missing include
targets and continue building.
"""

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.ValidationMissingFiles / "missing_include_file")


def test_wheel(project, project_path, assert_wheel_build, caplog):
    with project(project_path):
        assert_wheel_build(project_path)
        assert_that(caplog.text).contains(
            "Pattern 'missing-include-file.txt' resolved nothing"
        )


def test_sdist(project, project_path, assert_sdist_build, caplog):
    with project(project_path):
        assert_sdist_build(project_path)
        assert_that(caplog.text).contains(
            "Pattern 'missing-include-file.txt' resolved nothing"
        )
