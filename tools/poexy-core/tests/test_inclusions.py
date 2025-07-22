from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.packages.files import FORBIDDEN_DIRS


@pytest.fixture()
def project_path(sample_project):
    return sample_project("includes")


def test_wheel(
    project,
    project_path,
    install_path,
    site_packages_path,
    dist_package_name,
    default_python_tag,
    wheel_data_purelib_folder,
    assert_wheel_build,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py"
            ]
        )

        purelib_path = site_packages_path / "includes"
        data_path = install_path / "share" / "includes"

        assert_that(purelib_path.exists()).is_true()
        assert_that(data_path.exists()).is_true()

        purelib_path = purelib_path.relative_to(install_path)
        data_path = data_path.relative_to(install_path)
        purelib_glob_pattern = f"{purelib_path}/**/*"
        data_glob_pattern = f"{data_path}/**/*"

        for file in install_path.rglob(purelib_glob_pattern):
            if not file.is_file():
                continue
            if any(part in FORBIDDEN_DIRS for part in file.parts):
                continue
            assert_that(file.suffix).is_equal_to(".py")

        for file in install_path.rglob(data_glob_pattern):
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
