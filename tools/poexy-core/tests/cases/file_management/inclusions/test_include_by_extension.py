"""
Test case: Including files by file extension patterns

This test verifies that poexy-core correctly handles include patterns that
target specific file extensions. This tests pattern matching for extension-based
inclusions and ensures proper glob pattern processing for file types.

Test scenario:
- A pyproject.toml file specifies include patterns for specific file extensions
- The project contains files with various extensions, some matching includes
- The build system should only include files matching the extension patterns
- Only files with included extensions should remain in the package

Expected behavior:
- Files matching included extension patterns are properly included
- Extension matching is case-sensitive or case-insensitive as appropriate
- Glob patterns for extensions work correctly (e.g., "*.py", "**/*.txt")
- File filtering occurs consistently across all package formats

Edge case significance:
This tests extension-based inclusion which is commonly used to include
source files, documentation, or other relevant files. Proper extension
handling ensures clean packages with only the desired file types and validates
glob pattern matching for one of the most common include use cases.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "include_by_extension")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "file_to.include",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "some_folder"
                / "file_to.include",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = venv.site_package / dist_package_name() / "file_to.include"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package / dist_package_name() / "some_folder" / "file_to.include"
        )
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
                Path("src") / "file_to.include",
                Path("src") / "some_folder" / "file_to.include",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = venv.site_package / dist_package_name() / "file_to.include"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package / dist_package_name() / "some_folder" / "file_to.include"
        )
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
