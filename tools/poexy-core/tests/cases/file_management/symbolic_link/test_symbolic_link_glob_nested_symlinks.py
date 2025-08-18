"""
Test case: Glob resolution integration with symlinks
  (directory target including a symlink)

This test verifies that when a directory is selected via a glob pattern, its
contents are collected, including any symbolic links contained within the
directory. The symlink inside the selected directory must be analyzed and
validated as part of the inclusion. No invalid scenarios are covered in this test.

Test scenario:
- A glob pattern matches an in-project directory
- The matched directory contains a symlink among its children

Expected behavior:
- The directory is included along with its regular children and the symlink
- The symlink inside the directory is analyzed and validated as part of
  the collection process, identically to a direct selection case

Edge case significance:
Ensures that directory selection via globs does not skip or treat differently
symlinks that are nested within included directories when all inputs are valid.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "symlink-subtargets-file:ln",
    "whl:symlink-targets/included:ln",
    "whl:symlink-targets/included.py:ln",
    "whl:symlink-targets/subtargets/included:ln",
    "whl:symlink-targets/subtargets/included.py:ln",
    "tar:symlink-targets:ln",
    "whl:symlink-targets/symlink/included:ln",
    "whl:symlink-targets/symlink/included.py:ln",
    "tar:symlink-targets/symlink:ln",
    "whl:symlink-subtargets/included:ln",
    "whl:symlink-subtargets/included.py:ln",
    "tar:symlink-subtargets:ln",
    "targets/included",
    "targets/included.py",
    "whl:targets/symlink/included:ln",
    "whl:targets/symlink/included.py:ln",
    "tar:targets/symlink:ln",
    "targets/subtargets/included",
    "targets/subtargets/included.py",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_glob_nested_symlinks"
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
