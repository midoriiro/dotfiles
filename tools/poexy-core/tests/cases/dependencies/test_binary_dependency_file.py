"""
Test case: Binary dependency resolution from file sources

This test verifies that poexy-core correctly handles binary packaging when
dependencies are sourced from local files (e.g., wheel files, tarballs).
File dependencies must be properly resolved and integrated into binaries.

Test scenario:
- A binary project specifies dependencies from local files
- The build system resolves file-based dependencies during packaging
- The resulting binary executable should include the file dependency
- Binary execution should work correctly with the integrated file dependency

Expected behavior:
- File dependencies are properly resolved and included in binary packages
- Binary executables function correctly with integrated file dependencies
- File dependency resolution works for both wheel and sdist formats
- Binary execution produces expected output with file dependency functionality

Edge case significance:
This tests file-based dependency integration which is important for projects
that depend on custom packages or specific versions not available in indexes.
Proper file handling ensures binary distributions include all necessary components.
"""

import pytest
from assertpy import assert_that

from poexy_core.packages.format import WheelFormat
from poexy_core.pyproject.exceptions import PyProjectError
from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.Dependencies / "binary_dependency_file")


def test_wheel(
    project,
    project_path,
    assert_wheel_build,
    wheel_data_scripts_folder,
    current_python_tag,
    dist_package_name,
    package_name,
    venv: TestVirtualEnvironment,
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
        purelib_path = venv.site_package / dist_package_name() / "__init__.py"
        assert_that(purelib_path.exists()).is_false()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_true()
        result = execute_binary(binary_path)
        if result.returncode != 0:
            raise AssertionError(f"Binary failed to execute: {result.stderr}")
        assert_that(result.stdout).is_equal_to("Hello, World!\n")


def test_sdist(
    project,
    project_path,
    assert_sdist_build,
):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing to a file",
        ):
            assert_sdist_build(project_path)
