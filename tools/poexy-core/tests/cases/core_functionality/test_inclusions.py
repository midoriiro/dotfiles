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

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.packages.files import FORBIDDEN_DIRS
from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.CoreFunctionality / "includes")


def test_wheel(
    project,
    project_path,
    venv: TestVirtualEnvironment,
    dist_package_name,
    default_python_tag,
    wheel_data_purelib_folder,
    wheel_data_data_folder,
    assert_wheel_build,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
                wheel_data_data_folder(default_python_tag)
                / "share"
                / dist_package_name()
                / "docs"
                / "test.md",
                wheel_data_data_folder(default_python_tag)
                / "share"
                / dist_package_name()
                / "docs"
                / "subdir"
                / "subsubdir"
                / "test.md",
            ],
            strict=True,
        )

        purelib_path = venv.site_package / "includes"
        data_path = venv.path / "share" / "includes"

        assert_that(purelib_path.exists()).is_true()
        assert_that(data_path.exists()).is_true()

        purelib_path = purelib_path.relative_to(venv.path)
        data_path = data_path.relative_to(venv.path)
        purelib_glob_pattern = f"{purelib_path}/**/*"
        data_glob_pattern = f"{data_path}/**/*"

        for file in purelib_path.rglob(purelib_glob_pattern):
            if not file.is_file():
                continue
            if any(part in FORBIDDEN_DIRS for part in file.parts):
                continue
            assert_that(file.suffix).is_equal_to(".py")

        for file in data_path.rglob(data_glob_pattern):
            if not file.is_file():
                continue
            if any(part in FORBIDDEN_DIRS for part in file.parts):
                continue
            assert_that(file.suffix).is_equal_to(".md")


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("module.py"),
                Path("src") / "__init__.py",
                Path("docs") / "test.md",
                Path("docs") / "test.txt",
                Path("docs") / "subdir" / "test.txt",
                Path("docs") / "subdir" / "test.rst",
                Path("docs") / "subdir" / "subsubdir" / "test.txt",
                Path("docs") / "subdir" / "subsubdir" / "test.md",
            ],
            strict=True,
        )
