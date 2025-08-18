"""
Test case: Self-building capability and build system API

This test verifies that poexy-core can successfully build itself using its own
build system API. Self-building tests the completeness and correctness of the
build system implementation and validates core API functionality.

Test scenario:
- The build system API is used to query build requirements and prepare metadata
- The poexy-core project itself is built using its own build system
- Build requirements are properly returned by the API functions
- The resulting packages contain the expected build system components

Expected behavior:
- Build requirements are correctly returned by get_requires_for_build_wheel()
- Metadata preparation creates properly named dist-info directories
- Self-building produces working wheel and sdist packages
- The build system components are correctly included in built packages

Edge case significance:
This tests build system completeness and self-consistency which is crucial for
reliability. A build system that can build itself demonstrates functional
completeness and provides confidence in its ability to handle other projects.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core import api
from tests.utils.venv import TestVirtualEnvironment


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


@pytest.mark.prevent_venv_self_build()
@pytest.mark.serial
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


@pytest.mark.prevent_venv_self_build()
@pytest.mark.serial
def test_sdist(
    self_project,
    dist_package_name,
    venv: TestVirtualEnvironment,
    assert_sdist_build,
):
    assert_tar_file = assert_sdist_build(self_project)
    assert_tar_file(
        [
            Path(dist_package_name()) / "api.py",
            Path("tests") / "conftest.py",
        ]
    )

    site_packages = venv.site_package / dist_package_name()
    assert_that(str(site_packages)).is_directory()
