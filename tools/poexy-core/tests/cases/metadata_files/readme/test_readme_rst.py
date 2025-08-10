"""
Test case: README file in reStructuredText format

This test verifies that poexy-core correctly handles README files in
reStructuredText (RST) format. RST files should be properly detected,
processed, and included with correct content type metadata.

Test scenario:
- A project has a README file with .rst extension
- The README contains valid reStructuredText markup
- The build system processes the RST README for package metadata
- Content type should be automatically detected as text/x-rst

Expected behavior:
- RST files are automatically detected from .rst extension
- README content is properly included in package metadata
- Content type is correctly set to "text/x-rst" in package manifest
- RST content and formatting are preserved in package description

Edge case significance:
This tests RST format support which is important for Python ecosystem
compatibility. RST is a traditional documentation format in Python and
proper handling ensures compatibility with existing documentation workflows.
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
    return sample_project(SamplePaths.MetadataFilesReadme / "readme-rst")


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
                Path("README.rst"),
            ],
            strict=True,
        )
        pkginfo_manifest = assert_pkginfo_manifest()
        assert_that(
            pkginfo_manifest.get(MetadataField.DescriptionContentType)
        ).is_equal_to("text/x-rst")
        assert_that(pkginfo_manifest.get(MetadataField.Description)).is_equal_to(
            "I'm super informative\n====================\n\nAnd also multilines"
        )
