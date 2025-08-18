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

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "resources/data.txt:purelib",
    "resources/nested/data.json:purelib",
    "resources/nested/deeper/deep.txt:purelib",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "include_entire_directory"
    )


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    assert_venv_files,
    prepare_zip_files,
    prepare_venv_files,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)

        zip_files = AssertPaths(expected_files)
        prepare_zip_files(zip_files)

        assert_zip_file(
            zip_files,
            strict=True,
        )

        venv_files = AssertPaths(expected_files)
        prepare_venv_files(venv_files)
        assert_venv_files(venv_files)


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    assert_venv_files,
    prepare_tar_files,
    prepare_venv_files,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)

        tar_files = AssertPaths(expected_files)
        prepare_tar_files(tar_files)

        assert_tar_file(
            tar_files,
            strict=True,
        )

        venv_files = AssertPaths(expected_files)
        prepare_venv_files(venv_files)
        assert_venv_files(venv_files)
