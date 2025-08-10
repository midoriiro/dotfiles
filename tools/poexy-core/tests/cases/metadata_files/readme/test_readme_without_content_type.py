"""
Test case: README file without explicit content type specification

This test verifies that poexy-core correctly handles README files when no
explicit content type is specified in metadata. The system should auto-detect
the content type based on file extension and include proper metadata.

Test scenario:
- A project has a README file but no explicit content-type in metadata
- The README file has a recognizable extension (e.g., .md, .rst)
- The build system processes the README for package metadata
- Content type should be automatically determined from file extension

Expected behavior:
- Content type is automatically detected from file extension
- README content is properly included in package metadata
- Detected content type is correctly set in package manifest
- Auto-detection works consistently across wheel and sdist formats

Edge case significance:
This tests automatic content type detection which simplifies configuration
for users. Auto-detection reduces boilerplate in pyproject.toml while ensuring
proper README handling for common file formats like Markdown and RST.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.metadata.fields import MetadataField
from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.MetadataFilesReadme / "readme-without-content-type"
    )


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py"
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()


def test_sdist(project, project_path, assert_sdist_build, assert_pkginfo_manifest):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
                Path("README.md"),
            ],
            strict=True,
        )
        pkginfo_manifest = assert_pkginfo_manifest()
        assert_that(
            pkginfo_manifest.get(MetadataField.DescriptionContentType)
        ).is_equal_to("text/markdown")
        assert_that(pkginfo_manifest.get(MetadataField.Description)).is_equal_to(
            "# I'm super informative\n\nAnd also multilines"
        )
