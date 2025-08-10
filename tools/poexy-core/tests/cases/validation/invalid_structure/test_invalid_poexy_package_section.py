"""
Test case: Missing [tool.poexy.package] section in pyproject.toml

This test verifies that poexy-core properly handles and reports errors when the
[tool.poexy.package] section is absent in pyproject.toml. The package section is
required to define which package should be built and how it should be built.

Test scenario:
- A pyproject.toml file does not contain a [tool.poexy.package] section
- The build system reads the configuration
- An appropriate error should be raised indicating the missing section
- The build process should stop before attempting package creation

Expected behavior:
- A PyProjectError is raised stating "[tool.poexy.package] section not found"
- No build artifacts are created when the section is missing
- Both wheel and sdist builds fail consistently with the same error

Edge case significance:
This validates mandatory configuration for package resolution. Ensuring the
presence of [tool.poexy.package] prevents ambiguous or implicit package
selection.
"""

import re

import pytest

from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.ValidationInvalidStructure / "invalid_poexy_package_section"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[tool.poexy.package] section not found"),
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[tool.poexy.package] section not found"),
        ):
            assert_sdist_build(project_path)
