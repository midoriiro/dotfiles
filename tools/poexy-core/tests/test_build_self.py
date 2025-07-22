from pathlib import Path

from assertpy import assert_that

from poexy_core import api


def test_get_requires_for_build_wheel():
    requires = api.get_requires_for_build_wheel()
    assert_that(requires).is_not_empty()


def test_prepare_metadata_for_build_wheel(tmp_path, dist_package_name, package_version):
    metadata_name = api.prepare_metadata_for_build_wheel(str(tmp_path))

    dist_package_name = dist_package_name()
    package_version = package_version()
    assert_that(metadata_name).is_equal_to(
        f"{dist_package_name}-{package_version}.dist-info"
    )


def test_wheel(
    self_project,
    dist_package_name,
    default_python_tag,
    wheel_data_purelib_folder,
    assert_wheel_build,
):
    assert_zip_file = assert_wheel_build(self_project)
    assert_zip_file(
        [
            wheel_data_purelib_folder(default_python_tag)
            / dist_package_name()
            / "api.py",
        ]
    )


def test_sdist(
    self_project,
    dist_package_name,
    site_packages_path,
    assert_sdist_build,
):
    assert_tar_file = assert_sdist_build(self_project)
    assert_tar_file(
        [
            Path(dist_package_name()) / "api.py",
            Path("tests") / "conftest.py",
        ]
    )

    site_packages = site_packages_path / dist_package_name()
    assert_that(str(site_packages)).is_directory()
