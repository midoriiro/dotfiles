"""
Test case: License specification using license file

This test verifies that poexy-core correctly handles license specification when
a license file is provided. License files should be properly included in
packages and referenced in metadata for legal compliance and distribution.

Test scenario:
- A project specifies a license using a license file (e.g., LICENSE, LICENSE.txt)
- The license file exists and contains valid license text
- The build system processes the license file for package inclusion
- License file metadata should be properly set in package manifest

Expected behavior:
- License file is included in both wheel and sdist packages
- License file is copied to appropriate location in wheel (licenses/ directory)
- License file metadata field is correctly set to reference the file
- License file inclusion is consistent across package formats

Edge case significance:
This tests standard license file handling which is essential for legal
compliance in package distribution. Proper license file inclusion ensures
that legal terms are preserved and accessible in distributed packages.
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
    return sample_project(SamplePaths.MetadataFilesLicence / "license-file")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    wheel_dist_info_folder,
    default_python_tag,
    dist_package_name,
    venv: TestVirtualEnvironment,
    assert_metadata_manifest,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
                wheel_dist_info_folder(default_python_tag) / "licenses" / "LICENSE",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        metadata_manifest = assert_metadata_manifest(default_python_tag)
        assert_that(metadata_manifest.get(MetadataField.LicenseFile)).is_equal_to(
            "licences/LICENSE"
        )


def test_sdist(project, project_path, assert_sdist_build, assert_pkginfo_manifest):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
                Path("LICENSE"),
            ],
            strict=True,
        )
        pkginfo_manifest = assert_pkginfo_manifest()
        assert_that(pkginfo_manifest.get(MetadataField.LicenseFile)).is_equal_to(
            "LICENSE"
        )
