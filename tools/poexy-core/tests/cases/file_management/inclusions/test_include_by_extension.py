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

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "file_to.include",
    "some_folder/file_to.include",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "include_by_extension")


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
