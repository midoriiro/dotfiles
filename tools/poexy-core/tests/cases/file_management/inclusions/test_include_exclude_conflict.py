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

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementInclusions / "include_exclude_conflict"
    )


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    assert_venv_files,
    prepare_zip_files,
    prepare_venv_files,
):
    with project(project_path):
        assert_zip_file = assert_wheel_build(project_path)

        zip_files = AssertPaths(expected_files)
        prepare_zip_files(zip_files)

        assert_zip_file(
            zip_files,
            strict=True,
        )

        venv_files = AssertPaths(expected_files)
        prepare_venv_files(venv_files)
        assert_venv_files(venv_files)


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
    assert_venv_files,
    prepare_tar_files,
    prepare_venv_files,
):
    with project(project_path):
        assert_tar_file = assert_sdist_build(project_path)

        tar_files = AssertPaths(expected_files)
        prepare_tar_files(tar_files)

        assert_tar_file(
            tar_files,
            strict=True,
        )

        venv_files = AssertPaths(expected_files)
        prepare_venv_files(venv_files)
        assert_venv_files(venv_files)
