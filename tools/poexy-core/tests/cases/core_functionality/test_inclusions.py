"""
Test case: File inclusion and exclusion with type-based distribution

This test verifies that poexy-core correctly handles file inclusion and exclusion
rules with proper type-based distribution to different package locations. Files
should be placed in appropriate directories based on their type and purpose.

Test scenario:
- A project specifies complex includes/excludes rules for various file types
- The project contains Python files, documentation files, and other content
- The build system processes inclusion rules and distributes files by type
- Python files should go to purelib, documentation files to data directories

Expected behavior:
- Python files (.py) are correctly placed in purelib directories
- Documentation files (.md) are correctly placed in data directories 
- File inclusion/exclusion rules are properly applied during packaging
- Forbidden directories are correctly excluded from package contents

Edge case significance:
This tests complex file management which is essential for projects with diverse
content types. Proper file type distribution ensures that packages are organized
correctly and that different file types are accessible in appropriate locations.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "tar:module.py:plat:data",
    "docs/test.md:plat:data",
    "tar:docs/test.txt:plat:data",
    "tar:docs/subdir/test.txt:plat:data",
    "tar:docs/subdir/test.rst:plat:data",
    "tar:docs/subdir/subsubdir/test.txt:plat:data",
    "docs/subdir/subsubdir/test.md:plat:data",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.CoreFunctionality / "includes")


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
