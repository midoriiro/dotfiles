"""
Test case: Include a file from a non-source project subfolder into the platform data
directory

This test specifies the behavior of include patterns that point to a single file
located under the project root but outside the "src/" tree (for example,
"some_folder/file_to.include").

Test scenario:
- The `pyproject.toml` declares an include rule targeting that file.
- The project contains the targeted file.
- The build process must bundle the file and install it into the platform data
  directory.

Expected behavior:
- The targeted file is bundled into both sdist and wheel artifacts.
- In the wheel, the file is placed under the platform data directory path.
- Path resolution is safe and deterministic.
- Only the explicitly included file is added; no unintended traversal or directory
  leakage occurs.

Scope:
- This test focuses on including a single file into the platform data directory.
  It does not validate root-level includes or broader globbing patterns.

Security and edge considerations:
- No directory traversal beyond the project boundary is allowed.
- Absolute paths are either rejected or normalized according to policy.
- Globs referencing parent directories are evaluated with an explicit allow-list.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "some_folder/file_to.include:plat:data",
    "!:$BINARY:bin",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "include_file_to_platform_directory"
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
