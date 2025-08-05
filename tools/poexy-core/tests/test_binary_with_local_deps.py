import pytest
from assertpy import assert_that

from poexy_core.packages.format import WheelFormat
from poexy_core.pyproject.exceptions import PyProjectError

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project("binary_with_local_deps")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_scripts_folder,
    current_python_tag,
    dist_package_name,
    package_name,
    site_packages_path,
    install_path,
    execute_binary,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path, _format={WheelFormat.Binary})
        assert_zip_file(
            [
                wheel_data_scripts_folder(current_python_tag) / package_name(),
            ],
            strict=True,
        )
        purelib_path = site_packages_path / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_false()
        binary_path = install_path / "bin" / package_name()
        assert_that(binary_path.exists()).is_true()
        result = execute_binary(binary_path)
        if result.returncode != 0:
            raise AssertionError(f"Binary failed to execute: {result.stderr}")
        assert_that(result.stdout).is_equal_to("Hello, World!\n")


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing only to local dependencies",
        ):
            assert_sdist_build(project_path)
