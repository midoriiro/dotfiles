"""
Test case: Deprecated license file format with backward compatibility

This test verifies that poexy-core correctly handles license files specified
using deprecated configuration formats while maintaining backward compatibility.
Some older license file specifications may still work but use outdated metadata.

Test scenario:
- A project specifies a license file using deprecated configuration format
- The license file exists and contains valid license text
- The build system processes the deprecated license file specification
- License should still be included despite using deprecated format

Expected behavior:
- License file is included in both wheel and sdist packages despite deprecated format
- License file is copied to appropriate location in wheel packages
- License file metadata is correctly populated using current standards
- Backward compatibility maintains existing functionality

Edge case significance:
This tests backward compatibility for deprecated license file formats which
is important for maintaining existing project compatibility. Proper handling
ensures existing projects continue to work while encouraging modern practices.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.metadata.fields import MetadataField
from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.MetadataFilesLicence / "license-deprecated-file")


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
