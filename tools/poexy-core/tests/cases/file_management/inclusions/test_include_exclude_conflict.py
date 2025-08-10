"""
Test case: Conflicting include and exclude rules for the same file

This test verifies that poexy-core correctly handles the edge case where the
same file or pattern is specified in both includes and excludes sections.
This tests rule precedence and conflict resolution in file selection logic.

Test scenario:
- A pyproject.toml file specifies the same file/pattern in both includes and excludes
- The build system processes these conflicting rules during file selection
- A deterministic precedence rule should be applied (exclude vs include priority)
- The final package should reflect the resolved conflict consistently

Expected behavior:
- Conflicting rules are resolved with clear precedence (typically exclude wins)
- The resolution behavior is consistent across wheel and sdist builds
- Warning messages may be generated to inform about the conflict
- Final file selection matches the documented precedence rules

Edge case significance:
This tests rule conflict resolution which can occur in complex configurations
or when rules are inherited/merged from multiple sources. Clear precedence
handling prevents unpredictable package contents and ensures reproducible
builds. Proper conflict resolution helps developers understand rule interactions.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "include_exclude_conflict"
    )


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_purelib_folder,
    default_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)
        assert_tar_file(
            [
                Path("src") / "__init__.py",
            ],
            strict=True,
        )
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
