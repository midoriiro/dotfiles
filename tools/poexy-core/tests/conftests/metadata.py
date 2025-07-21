import sys
from pathlib import Path
from typing import Callable

import pytest
from assertpy import assert_that
from poetry.core.masonry.utils.helpers import distribution_name

from poexy_core.builders.builder import PythonTag
from poexy_core.builders.sdist import SdistMetadata
from poexy_core.builders.wheel import WheelMetadata

# pylint: disable=redefined-outer-name


@pytest.fixture()
def default_python_tag():
    return PythonTag(impl="py", major=sys.version_info.major)


@pytest.fixture()
def current_python_tag():
    return PythonTag.from_current_environment()


@pytest.fixture()
def package_name(pyproject) -> Callable[[], str]:
    def _package_name():
        return pyproject().poetry.package.name

    return _package_name


@pytest.fixture()
def dist_package_name(pyproject) -> Callable[[], str]:
    def _dist_package_name():
        return distribution_name(pyproject().poetry.package.name)

    return _dist_package_name


@pytest.fixture()
def package_version(pyproject) -> Callable[[], str]:
    def _package_version():
        return pyproject().poetry.package.version.to_string()

    return _package_version


@pytest.fixture()
def wheel_metadata(
    dist_temp_path, dist_package_name, package_version
) -> Callable[[PythonTag], WheelMetadata]:
    def _wheel_metadata(python_tag: PythonTag) -> WheelMetadata:
        metadata = WheelMetadata(
            dist_temp_path, dist_package_name(), package_version(), python_tag
        )
        assert_that(str(metadata.archive_path)).exists()
        return metadata

    return _wheel_metadata


@pytest.fixture()
def wheel_dist_info_folder(wheel_metadata) -> Callable[[PythonTag], Path]:
    def _wheel_dist_info_folder(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        dist_info_folder = metadata.dist_info_folder
        dist_info_folder = dist_info_folder.relative_to(metadata.root_folder)
        return dist_info_folder

    return _wheel_dist_info_folder


@pytest.fixture()
def wheel_data_purelib_folder(wheel_metadata) -> Callable[[PythonTag], Path]:
    def _wheel_data_purelib_folder(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        data_purelib_folder = metadata.data_purelib_folder
        data_purelib_folder = data_purelib_folder.relative_to(metadata.root_folder)
        return data_purelib_folder

    return _wheel_data_purelib_folder


@pytest.fixture()
def wheel_data_scripts_folder(wheel_metadata) -> Callable[[PythonTag], Path]:
    def _wheel_data_scripts_folder(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        data_scripts_folder = metadata.data_scripts_folder
        data_scripts_folder = data_scripts_folder.relative_to(metadata.root_folder)
        return data_scripts_folder

    return _wheel_data_scripts_folder


@pytest.fixture()
def sdist_metadata(
    dist_temp_path, dist_package_name, package_version
) -> Callable[[], SdistMetadata]:
    def _sdist_metadata():
        metadata = SdistMetadata(dist_temp_path, dist_package_name(), package_version())
        assert_that(str(metadata.archive_path)).exists()
        return metadata

    return _sdist_metadata
