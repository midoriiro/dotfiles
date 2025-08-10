"""
Test case: Excluding entire directories with recursive content

This test verifies that poexy-core correctly handles excludes that specify
entire directories, ensuring all subdirectories and files are recursively
excluded. This tests recursive directory exclusion behavior and completeness.

Test scenario:
- A pyproject.toml file specifies entire directories in excludes section
- The directories contain nested subdirectories and various file types
- The build system should recursively exclude all directory contents
- Excluded directories should not appear in the final package

Expected behavior:
- All files and subdirectories are recursively excluded from specified directories
- No trace of excluded directory structure remains in the package
- Exclusion applies to all nested content without manual specification
- Both immediate files and deeply nested content are excluded

Edge case significance:
This tests recursive directory exclusion which is important for removing
test directories, development files, or unwanted resource directories. Complete
directory exclusion ensures that sensitive or irrelevant directory structures
are completely omitted from packages without requiring individual file exclusions.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "exclude_entire_directory"
    )


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
