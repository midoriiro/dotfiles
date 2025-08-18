"""
Test case: Glob pattern matching symbolic link with literal name (file target)

This test verifies that poexy-core correctly handles a symbolic link when it
is included via a literal glob pattern that matches the symlink by its exact name
(no wildcard patterns), where the symlink resolves to a regular file.

Test scenario:
- A symlink exists in the source directory pointing to a regular file
- The inclusion glob pattern is literal, matching the symlink by its exact name 
  (e.g., "mylink")
- No wildcard patterns or glob expansions are used, just the literal name of the symlink

Expected behavior:
- The symlink is correctly identified and included via the literal name match
- The file target is resolved and handled according to symlink resolution policy
- Package build succeeds with the symlink content properly included
- Both wheel and sdist builds handle the literal symlink inclusion correctly

Edge case significance:
Ensures that literal name-based inclusion of symlinks (without wildcard patterns)
works correctly when the target is a file, validating the glob resolution
system's handling of literal symlink name matches.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = ["__init__.py", "symlink:ln", "target"]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_glob_literal_file_target"
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
