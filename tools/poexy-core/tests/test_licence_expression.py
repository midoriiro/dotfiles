from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.metadata.fields import MetadataField

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project("license-expression")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    site_packages_path,
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
        purelib_path = site_packages_path / dist_package_name() / "__init__.py"
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
