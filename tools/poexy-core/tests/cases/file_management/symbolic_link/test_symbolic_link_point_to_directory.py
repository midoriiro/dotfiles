"""
Test case: Symbolic link pointing to a directory

This test verifies that poexy-core correctly handles a symbolic link in the
source directory whose final resolved target is a directory.

Test scenario:
- A symlink exists in the source directory pointing (directly or via a chain)
  to a directory inside the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- Directory traversal protections are applied consistently
- The symlink is handled in a predictable way: followed, preserved, or resolved
  according to project policy
- Package integrity is maintained

Edge case significance:
Ensures directory-target symlinks do not lead to accidental traversal or
ambiguous inclusion of files during builds.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "!:symlink:ln",
    "!:target/not-included",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink / "symbolic_link_point_to_directory"
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
