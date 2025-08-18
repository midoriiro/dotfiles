"""
Test case: Glob resolution integration with symlinks (directory targets)

This test verifies that when package paths are selected via glob patterns, any
matched symbolic links that resolve to directories are included and validated
exactly like direct directory paths. No invalid scenarios are covered in this test.

Test scenario:
- A glob pattern matches one or more symlinks in the source directory
- Targets include a valid in-project directory only

Expected behavior:
- The referenced directory and what it includes are collected as expected
- Standard validations (existence, project boundary, accessibility) are applied
  and pass identically to direct directory selection

Edge case significance:
Ensures symmetry between explicit directory selection and glob-driven selection
for directory-resolving symbolic links when all inputs are valid.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "whl:symlink/included:ln",
    "whl:symlink/included.py:ln",
    "tar:symlink:ln",
    "targets/included",
    "targets/included.py",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_glob_pattern_directory_target"
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
