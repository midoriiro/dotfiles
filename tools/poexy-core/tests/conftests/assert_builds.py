import tarfile
import zipfile
from pathlib import Path
from typing import Callable, List, Set

import pytest
from assertpy import assert_that

from poexy_core import api
from poexy_core.builders.wheel import WheelMetadata
from poexy_core.packages.format import WheelFormat

# pylint: disable=redefined-outer-name,dangerous-default-value

__all__ = [
    "assert_tar_file",
    "assert_zip_file",
    "assert_wheel_build",
    "assert_sdist_build",
]


@pytest.fixture()
def assert_tar_file() -> Callable[[Path, List[Path], bool], None]:
    def _assert(archive_path: Path, expected_files: List[Path], strict: bool = False):
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            assert_that(members).is_not_empty()

            archive_file_paths = [Path(member.name) for member in members]

            for member in archive_file_paths:
                if member.name == "PKG-INFO":
                    root_folder = member.parent
                    break

            assert_that(root_folder).is_not_none()

            archive_file_paths = [
                Path(member.name).relative_to(root_folder) for member in members
            ]

            if strict:
                # Assert that all expected files are present and no extra files exist
                archive_file_paths = [
                    path
                    for path in archive_file_paths
                    if path.name not in ["PKG-INFO", "pyproject.toml"]
                ]
                assert_that(len(archive_file_paths)).is_equal_to(len(expected_files))
                assert_that(sorted(archive_file_paths)).is_equal_to(
                    sorted(expected_files)
                )
            else:
                # Assert that all expected files are present (partial check)
                for expected_file in expected_files:
                    assert_that(archive_file_paths).contains(expected_file)

    return _assert


@pytest.fixture()
def assert_zip_file() -> Callable[[Path, List[Path], bool], None]:
    def _assert(
        archive_path: Path,
        expected_files: List[Path],
        strict: bool = False,
        strip: bool = True,
    ):
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            members = zip_file.namelist()
            assert_that(members).is_not_empty()

            archive_file_paths = [Path(member) for member in members]

            if strict:
                # Assert that all expected files are present and no extra files exist
                if strip:
                    archive_file_paths = [
                        path
                        for path in archive_file_paths
                        if path.name not in ["WHEEL", "METADATA", "RECORD"]
                    ]
                assert_that(len(archive_file_paths)).is_equal_to(len(expected_files))
                assert_that(sorted(archive_file_paths)).is_equal_to(
                    sorted(expected_files)
                )
            else:
                # Assert that all expected files are present (partial check)
                for expected_file in expected_files:
                    assert_that(archive_file_paths).contains(expected_file)

    return _assert


@pytest.fixture()
def assert_wheel_build(
    project,
    dist_path,
    install_path,
    dist_package_name,
    package_name,
    site_packages_path,
    current_python_tag,
    default_python_tag,
    wheel_metadata,
    wheel_data_scripts_folder,
    assert_metadata_manifest,
    assert_wheel_manifest,
    assert_record_manifest,
    assert_pip_install,
    assert_zip_file,
) -> Callable[[Path], Callable[[List[Path], bool], None]]:
    def _assert(project_path: Path, _format: Set[WheelFormat] = {WheelFormat.Source}):
        with project(project_path):
            filename = api.build_wheel(str(dist_path))

            assert_that(filename).ends_with(".whl")
            assert_that(filename).starts_with(dist_package_name())
            archive_path = dist_path / filename
            assert_that(str(archive_path)).is_file()
            assert_that(zipfile.is_zipfile(archive_path)).is_true()

            if len(_format) == 1 and WheelFormat.Binary in _format:
                python_tag = current_python_tag
            else:
                python_tag = default_python_tag

            metadata: WheelMetadata = wheel_metadata(python_tag)
            assert_metadata_manifest(python_tag)
            assert_wheel_manifest(python_tag)
            assert_record_manifest(python_tag)
            assert_pip_install(archive_path)

            site_packages = site_packages_path / dist_package_name()

            if len(_format) == 1 and WheelFormat.Binary in _format:
                assert_that(str(site_packages)).does_not_exist()
                binary_path = install_path / "bin" / package_name()
                assert_that(binary_path.exists()).is_true()
                dist_info_folder = metadata.dist_info_folder.name
                assert_zip_file(
                    archive_path,
                    [
                        Path(dist_info_folder) / "WHEEL",
                        Path(dist_info_folder) / "METADATA",
                        Path(dist_info_folder) / "RECORD",
                        wheel_data_scripts_folder(python_tag) / package_name(),
                    ],
                    strict=True,
                    strip=False,
                )
            else:
                assert_that(str(site_packages)).exists()
                binary_path = install_path / "bin" / package_name()
                if WheelFormat.Binary in _format:
                    assert_that(binary_path.exists()).is_true()
                else:
                    assert_that(binary_path.exists()).is_false()
                dist_info_folder = metadata.dist_info_folder.name
                expected_zip_files = [
                    Path(dist_info_folder) / "WHEEL",
                    Path(dist_info_folder) / "METADATA",
                    Path(dist_info_folder) / "RECORD",
                ]
                if WheelFormat.Binary in _format:
                    expected_zip_files.append(
                        wheel_data_scripts_folder(python_tag) / package_name()
                    )
                assert_zip_file(archive_path, expected_zip_files)

            def _assert_zip_file(expected_files: List[Path], strict: bool = False):
                assert_zip_file(archive_path, expected_files, strict)

            return _assert_zip_file

    return _assert


@pytest.fixture()
def assert_sdist_build(
    project,
    dist_path,
    site_packages_path,
    install_path,
    dist_package_name,
    package_name,
    assert_pkginfo_manifest,
    assert_pip_wheel,
    assert_pip_install,
    assert_tar_file,
) -> Callable[[Path], Callable[[List[Path], bool], None]]:
    def _assert(project_path: Path, _format: Set[WheelFormat] = {WheelFormat.Source}):
        with project(project_path):
            filename = api.build_sdist(str(dist_path))

            assert_that(filename).ends_with(".tar.gz")
            assert_that(filename).starts_with(dist_package_name())
            archive_path = dist_path / filename
            assert_that(str(archive_path)).is_file()
            assert_that(tarfile.is_tarfile(archive_path)).is_true()

            assert_pkginfo_manifest()
            wheel_path = assert_pip_wheel(archive_path)
            assert_pip_install(wheel_path)

            site_packages = site_packages_path / dist_package_name()

            if len(_format) == 1 and WheelFormat.Binary in _format:
                assert_that(str(site_packages)).does_not_exist()
                binary_path = install_path / "bin" / package_name()
                assert_that(binary_path.exists()).is_true()
            else:
                assert_that(str(site_packages)).exists()
                binary_path = install_path / "bin" / package_name()
                if WheelFormat.Binary in _format:
                    assert_that(binary_path.exists()).is_true()
                else:
                    assert_that(binary_path.exists()).is_false()

            assert_tar_file(archive_path, [Path("pyproject.toml"), Path("PKG-INFO")])

            def _assert_tar_file(expected_files: List[Path], strict: bool = False):
                assert_tar_file(archive_path, expected_files, strict)

            return _assert_tar_file

    return _assert
