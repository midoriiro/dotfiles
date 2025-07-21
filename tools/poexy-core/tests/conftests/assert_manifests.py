from typing import Callable

import pytest
from assertpy import assert_that

from poexy_core.builders.builder import PythonTag
from poexy_core.manifest.manifest import (
    MetadataManifest,
    PackageInfoManifest,
    RecordManifest,
    WheelManifest,
)
from poexy_core.packages.files import FORBIDDEN_DIRS


@pytest.fixture()
def assert_metadata_manifest(
    wheel_metadata, package_name, package_version
) -> Callable[[PythonTag], MetadataManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        metadata_manifest = MetadataManifest(metadata.dist_info_folder)
        metadata_manifest.read()
        assert_that(metadata_manifest.get("Metadata-Version")).is_equal_to("2.4")
        assert_that(metadata_manifest.get("Name")).is_equal_to(package_name())
        assert_that(metadata_manifest.get("Version")).is_equal_to(package_version())
        return metadata_manifest

    return _assert


@pytest.fixture()
def assert_wheel_manifest(wheel_metadata) -> Callable[[PythonTag], WheelManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        wheel_manifest = WheelManifest(metadata.dist_info_folder)
        wheel_manifest.read()
        assert_that(wheel_manifest.get("Wheel-Version")).is_equal_to("1.0")
        assert_that(wheel_manifest.get("Generator")).is_equal_to("Poexy")
        if python_tag.platform is None:
            assert_that(wheel_manifest.get("Root-Is-Purelib")).is_equal_to("true")
        else:
            assert_that(wheel_manifest.get("Root-Is-Purelib")).is_equal_to("false")
        assert_that(wheel_manifest.get("Tag")).is_equal_to(f"{python_tag}")
        return wheel_manifest

    return _assert


@pytest.fixture()
def assert_record_manifest(wheel_metadata) -> Callable[[PythonTag], RecordManifest]:
    def _assert(python_tag: PythonTag):
        metadata = wheel_metadata(python_tag)
        record_manifest = RecordManifest(metadata.dist_info_folder)
        record_manifest.read()
        assert_that(len(record_manifest)).is_greater_than(1)
        for record in record_manifest:
            assert_that(FORBIDDEN_DIRS).does_not_contain(*record.path.parts)
        return record_manifest

    return _assert


@pytest.fixture()
def assert_pkginfo_manifest(
    sdist_metadata, package_name, package_version
) -> Callable[[], PackageInfoManifest]:
    def _assert():
        metadata = sdist_metadata()
        pkginfo_manifest = PackageInfoManifest(metadata.root_folder)
        pkginfo_manifest.read()
        assert_that(pkginfo_manifest.get("Metadata-Version")).is_equal_to("2.4")
        assert_that(pkginfo_manifest.get("Name")).is_equal_to(package_name())
        assert_that(pkginfo_manifest.get("Version")).is_equal_to(package_version())
        return pkginfo_manifest

    return _assert
