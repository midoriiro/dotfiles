"""
Test case: Excluding files by file extension patterns

This test verifies that poexy-core correctly handles exclude patterns that
target specific file extensions. This tests pattern matching for extension-based
exclusions and ensures proper glob pattern processing for file types.

Test scenario:
- A pyproject.toml file specifies exclude patterns for specific file extensions
- The project contains files with various extensions, some matching excludes
- The build system should filter out files matching the extension patterns
- Only files with non-excluded extensions should remain in the package

Expected behavior:
- Files matching excluded extension patterns are properly filtered out
- Extension matching is case-sensitive or case-insensitive as appropriate
- Glob patterns for extensions work correctly (e.g., "*.tmp", "**/*.log")
- File filtering occurs consistently across all package formats

Edge case significance:
This tests extension-based filtering which is commonly used to exclude
temporary files, build artifacts, or development-only files. Proper extension
handling ensures clean packages without unwanted file types and validates
glob pattern matching for one of the most common exclude use cases.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "exclude_by_extension")


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
                / "__init__.py"
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
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
            [Path("src") / "__init__.py"],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
