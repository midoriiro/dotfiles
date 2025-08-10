"""
Test case: License specification using SPDX license expression

This test verifies that poexy-core correctly handles license specification when
an SPDX license expression is provided instead of a license file. SPDX
expressions provide standardized license identification for package metadata.

Test scenario:
- A project specifies a license using an SPDX expression (e.g., "MIT", "Apache-2.0")
- No separate license file is provided, only the expression
- The build system processes the license expression for package metadata
- License expression should be properly set in package manifest

Expected behavior:
- SPDX license expression is correctly set in package metadata
- No license file is included in the package (expression-only)
- License expression metadata field is properly populated
- Expression handling is consistent across wheel and sdist formats

Edge case significance:
This tests SPDX expression support which provides a standardized way to
specify common licenses without including full license text files. This
approach is more efficient for well-known licenses and improves metadata.
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
    return sample_project(SamplePaths.MetadataFilesLicence / "license-expression")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
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
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        metadata_manifest = assert_metadata_manifest(default_python_tag)
        assert_that(metadata_manifest.get(MetadataField.LicenseExpression)).is_equal_to(
            "MIT"
        )


def test_sdist(project, project_path, assert_sdist_build, assert_pkginfo_manifest):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        pkginfo_manifest = assert_pkginfo_manifest()
        assert_that(pkginfo_manifest.get(MetadataField.LicenseExpression)).is_equal_to(
            "MIT"
        )
