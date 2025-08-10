"""
Test case: Multiple [tool.poexy.package] entries in pyproject.toml

This test verifies that poexy-core properly handles and reports errors when the
[tool.poexy.package] section contains more than one package definition. The
package section must be unique and define a single package to build.

Test scenario:
- A pyproject.toml file contains multiple package definitions under
  [tool.poexy.package]
- The build system reads the configuration
- An appropriate error should be raised indicating that only one definition is
  allowed
- The build process should stop before attempting package creation

Expected behavior:
- A PyProjectError is raised stating
  "[tool.poexy.package] section must contain only one package definition"
- No build artifacts are created when duplicates are present
- Both wheel and sdist builds fail consistently with the same error

Edge case significance:
This validates configuration uniqueness and prevents ambiguous or conflicting
package targets. Enforcing a single package definition ensures deterministic
build behavior.
"""

import re

import pytest

from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.ValidationInvalidStructure / "multiple_poexy_package_section"
    )


def test_wheel(project, project_path, assert_wheel_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape(
                "[tool.poexy.package] section must contain only one package definition"
            ),
        ):
            assert_wheel_build(project_path)


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match=re.escape(
                "[tool.poexy.package] section must contain only one package definition"
            ),
        ):
            assert_sdist_build(project_path)
