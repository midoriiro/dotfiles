"""
Test case: Including entire directories with recursive content

This test verifies that poexy-core correctly handles includes that specify
entire directories, ensuring all subdirectories and files are recursively
included. This tests recursive directory inclusion behavior and completeness.

Test scenario:
- A pyproject.toml file specifies entire directories in includes section
- The directories contain nested subdirectories and various file types
- The build system should recursively include all directory contents
- Directory structure should be preserved in the final package

Expected behavior:
- All files and subdirectories are recursively included from specified directories
- Directory structure and file hierarchy are preserved exactly
- File permissions and attributes are maintained during inclusion
- Both immediate files and deeply nested content are included

Edge case significance:
This tests recursive directory handling which is important for including
documentation, examples, or resource directories. Complete directory inclusion
ensures that complex directory structures are preserved and that packages
contain all intended content without manual specification of individual files.
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
        SamplePaths.FileManagementInclusions / "include_entire_directory"
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
                / "__init__.py",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "data.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "nested"
                / "data.json",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "nested"
                / "deeper"
                / "deep.txt",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package / dist_package_name() / "resources" / "data.txt"
        )
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package
            / dist_package_name()
            / "resources"
            / "nested"
            / "data.json"
        )
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package
            / dist_package_name()
            / "resources"
            / "nested"
            / "deeper"
            / "deep.txt"
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
                Path("src") / "resources" / "data.txt",
                Path("src") / "resources" / "nested" / "data.json",
                Path("src") / "resources" / "nested" / "deeper" / "deep.txt",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package / dist_package_name() / "resources" / "data.txt"
        )
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package
            / dist_package_name()
            / "resources"
            / "nested"
            / "data.json"
        )
        assert_that(purelib_path.exists()).is_true()
        purelib_path = (
            venv.site_package
            / dist_package_name()
            / "resources"
            / "nested"
            / "deeper"
            / "deep.txt"
        )
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
