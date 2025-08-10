"""
Test case: README file with invalid content type specification

This test verifies that poexy-core correctly handles and reports errors when an
invalid or unsupported content type is specified for a README file in project
metadata. Only valid MIME types should be accepted for README content.

Test scenario:
- A project specifies a README file with an invalid content type in metadata
- The content type is not recognized as a valid README format
- The build system attempts to process the README with the invalid type
- Appropriate validation errors should be raised for unsupported content types

Expected behavior:
- Invalid content types are detected during metadata validation
- Error messages clearly identify the unsupported content type
- Build fails early with clear messages about valid content type options
- Content type validation is consistent across wheel and sdist formats

Edge case significance:
This tests content type validation which is essential for proper README
rendering on package indexes like PyPI. Invalid content types can cause
README display failures or security issues with unsupported formats.
"""

import pytest

from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.MetadataFilesReadme / "readme-wrong-content-type")


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="is not a valid ReadmeContentType",
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            ValueError,
            match="is not a valid ReadmeContentType",
        ):
            assert_sdist_build(project_path)
