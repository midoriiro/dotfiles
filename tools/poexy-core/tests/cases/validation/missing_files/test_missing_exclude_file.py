"""
Test case: Missing file specified in excludes configuration

This test verifies that poexy-core properly handles missing files in exclude
patterns by logging warnings rather than raising errors. This validates the
non-blocking behavior for exclude pattern resolution.

Test scenario:
- A pyproject.toml file lists specific files in excludes section
- One or more of the listed files do not exist on the filesystem
- The build system attempts to exclude the specified files
- A warning should be logged but the build should continue successfully

Expected behavior:
- No ValidationError is raised when missing exclude files are detected
- A warning message is logged identifying the unresolved exclude pattern
- The build continues and completes successfully despite missing excluded files
- The warning occurs during the file collection phase of the build

Edge case significance:
This tests exclude pattern tolerance. Unlike includes, missing exclude files
should not break the build process since exclude patterns are often used
defensively to filter out files that may or may not exist. The system should
gracefully handle missing exclude targets and continue building.
"""

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.ValidationMissingFiles / "missing_exclude_file")


def test_wheel(project, project_path, assert_wheel_build, caplog):
    with project(project_path):
        assert_wheel_build(project_path)
        assert_that(caplog.text).contains(
            "No files resolved for exclude pattern 'missing-exclude-file.txt'"
        )


def test_sdist(project, project_path, assert_sdist_build, caplog):
    with project(project_path):
        assert_sdist_build(project_path)
        assert_that(caplog.text).contains(
            "No files resolved for exclude pattern 'missing-exclude-file.txt'"
        )
