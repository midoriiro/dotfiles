"""
Test case: Missing [tool.poexy.binary] section in pyproject.toml

This test verifies that poexy-core properly handles and reports errors when the
[tool.poexy.binary] section is absent in pyproject.toml. The binary section is
required to define how a binary entrypoint should be built and packaged.

Test scenario:
- A pyproject.toml file does not contain a [tool.poexy.binary] section
- The build system reads the configuration
- An appropriate error should be raised indicating the missing section
- The build process should stop before attempting binary creation

Expected behavior:
- A PyProjectError is raised stating "[tool.poexy.binary] section not found"
- No build artifacts are created when the section is missing
- Both wheel and sdist builds fail consistently with the same error

Edge case significance:
This validates mandatory configuration for binary packaging. Ensuring the
presence of [tool.poexy.binary] prevents ambiguous or implicit binary setup and
guarantees deterministic build behavior.
"""

import re

import pytest

from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.ValidationInvalidStructure
        / "missing_package_name_for_binary_section"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[project] section must contain a name"),
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape("[project] section must contain a name"),
        ):
            assert_sdist_build(project_path)
