"""
Test case: README file with ambiguous file extension

This test verifies that poexy-core correctly handles and reports errors when a
README file has an ambiguous or unrecognized extension that prevents automatic
content type detection. Ambiguous extensions require explicit content type.

Test scenario:
- A project has a README file with an ambiguous extension (e.g., .txt)
- No explicit content type is specified in metadata
- The build system attempts to auto-detect content type from extension
- Auto-detection fails due to ambiguous or unsupported extension

Expected behavior:
- Ambiguous extensions are detected and reported as errors
- Error messages clearly identify the problematic extension
- Error messages suggest specifying explicit content type
- Detection failure is consistent across wheel and sdist formats

Edge case significance:
This tests edge case handling for ambiguous file extensions which helps users
understand configuration requirements. Proper error reporting guides users
toward explicit content type specification for non-standard README formats.
"""

import pytest

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.MetadataFilesReadme / "readme-undetermined-suffix"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="Cannot determine content type from file extension: .txt",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="Cannot determine content type from file extension: .txt",
        ):
            assert_sdist_build(project_path)
