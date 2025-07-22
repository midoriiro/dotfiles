from pathlib import Path

import pytest
from assertpy import assert_that

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project("default")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    site_packages_path,
    install_path,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py"
            ],
            strict=True,
        )
        purelib_path = site_packages_path / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = install_path / "bin" / package_name()
        assert_that(binary_path.exists()).is_false()


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    package_name,
    install_path,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("default") / "__init__.py",
            ],
            strict=True,
        )
        binary_path = install_path / "bin" / package_name()
        assert_that(binary_path.exists()).is_false()
