"""
Test case: Binary dependency resolution with local dependencies

This test verifies that poexy-core correctly handles binary packaging when
dependencies are local packages. Local dependencies must be properly resolved
for wheel builds but may have restrictions for sdist distributions.

Test scenario:
- A binary project specifies local package dependencies
- The build system resolves local dependencies for wheel packaging
- Wheel builds should succeed with integrated local dependencies
- Sdist builds may fail due to local dependency limitations

Expected behavior:
- Local dependencies are properly integrated into wheel binary packages
- Binary executables function correctly with integrated local dependencies
- Wheel builds succeed and produce working binary executables
- Sdist builds may fail with appropriate error messages about local dependencies

Edge case significance:
This tests local dependency handling in binary packaging which is important
for development workflows. Different behavior between wheel and sdist formats
reflects the challenges of distributing packages with local dependencies.
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
    return sample_project(SamplePaths.Dependencies / "binary_dependency_local")


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


def test_sdist(project, project_path, assert_sdist_build):
    with project(project_path):
        with pytest.raises(
            PyProjectError,
            match="Dependency 'library' is pointing only to local dependencies",
        ):
            assert_sdist_build(project_path)
