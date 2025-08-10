"""
Test case: Dependencies with mixed local and remote sources

This test verifies that poexy-core correctly handles projects that have
dependencies from both local and remote sources. Mixed dependencies require
proper resolution and metadata generation for different source types.

Test scenario:
- A project specifies dependencies from both local and remote sources
- Remote dependencies use URL specifications (e.g., wheel files from HTTP)
- The build system processes mixed dependency types for package metadata
- Dependencies should be properly resolved and included in package manifest

Expected behavior:
- Remote URL dependencies are correctly specified in Requires-Dist metadata
- Local dependencies are handled appropriately based on their type
- Mixed dependency resolution works consistently across package formats
- Package metadata correctly references the remote dependency URLs

Edge case significance:
This tests mixed dependency resolution which is important for complex projects
that combine local development dependencies with remote published packages.
Proper handling ensures correct dependency resolution during installation.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.Dependencies / "dependency_mixed_local_remote")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    assert_metadata_manifest,
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
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()

        manifest = assert_metadata_manifest(default_python_tag)
        assert_that(manifest.get("Requires-Dist")).is_equal_to(
            "library @ http://localhost:8000/library-1.0.0-py3-none-any.whl"
        )


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    package_name,
    assert_pkginfo_manifest,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()

        manifest = assert_pkginfo_manifest()
        assert_that(manifest.get("Requires-Dist")).is_equal_to(
            "library @ http://localhost:8000/library-1.0.0-py3-none-any.whl"
        )
