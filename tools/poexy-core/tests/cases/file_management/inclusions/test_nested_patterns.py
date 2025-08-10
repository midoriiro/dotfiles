"""
Test case: Complex nested glob patterns in includes/excludes

This test verifies that poexy-core correctly handles complex nested glob
patterns that use advanced glob syntax like recursive wildcards, character
classes, and nested directory patterns. This tests sophisticated pattern matching.

Test scenario:
- A pyproject.toml file contains complex glob patterns with nested wildcards
- Patterns may include recursive (**), character classes ([]), and combinations
- The project structure matches some but not all of these complex patterns
- Pattern matching should work correctly according to glob specifications

Expected behavior:
- Complex glob patterns are parsed and executed correctly
- Recursive wildcard patterns (**) match nested directory structures
- Character classes and other advanced glob features work as expected
- Pattern matching performance remains acceptable for complex patterns

Edge case significance:
This tests advanced glob pattern support which is important for sophisticated
file selection rules. Complex patterns allow precise control over package
contents but require robust pattern matching implementation. Proper handling
ensures that advanced users can create sophisticated inclusion/exclusion rules.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from tests.conftests.paths import SamplePaths
from tests.utils.venv import TestVirtualEnvironment

# pylint: disable=redefined-outer-name


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "nested_patterns")


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
        # Positive presence checks in the archive (non-strict)
        assert_zip_file(
            [
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "__init__.py",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "a.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "b.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "c.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "nested"
                / "a_deep.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "nested"
                / "b_deep.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "nested"
                / "deeper"
                / "a_very_deep.txt",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "images"
                / "icon1.png",
                wheel_data_purelib_folder(default_python_tag)
                / dist_package_name()
                / "resources"
                / "images"
                / "icon2.png",
            ],
            strict=True,
        )
        base = venv.site_package / dist_package_name()
        for rel in [
            Path("__init__.py"),
            Path("resources/a.txt"),
            Path("resources/b.txt"),
            Path("resources/c.txt"),
            Path("resources/nested/a_deep.txt"),
            Path("resources/nested/b_deep.txt"),
            Path("resources/nested/deeper/a_very_deep.txt"),
            Path("resources/images/icon1.png"),
            Path("resources/images/icon2.png"),
        ]:
            assert_that((base / rel).exists()).is_true()
        for rel in [
            Path("resources/temp1.txt"),
            Path("resources/nested/temp2.txt"),
            Path("resources/nested/deeper/draft1.md"),
        ]:
            assert_that((base / rel).exists()).is_false()
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
                Path("src") / "resources" / "a.txt",
                Path("src") / "resources" / "b.txt",
                Path("src") / "resources" / "c.txt",
                Path("src") / "resources" / "nested" / "a_deep.txt",
                Path("src") / "resources" / "nested" / "b_deep.txt",
                Path("src") / "resources" / "nested" / "deeper" / "a_very_deep.txt",
                Path("src") / "resources" / "images" / "icon1.png",
                Path("src") / "resources" / "images" / "icon2.png",
            ],
            strict=True,
        )
        base = venv.site_package / dist_package_name()
        for rel in [
            Path("__init__.py"),
            Path("resources/a.txt"),
            Path("resources/b.txt"),
            Path("resources/c.txt"),
            Path("resources/nested/a_deep.txt"),
            Path("resources/nested/b_deep.txt"),
            Path("resources/nested/deeper/a_very_deep.txt"),
            Path("resources/images/icon1.png"),
            Path("resources/images/icon2.png"),
        ]:
            assert_that((base / rel).exists()).is_true()
        binary_path = venv.bin_path / package_name()
        assert_that(binary_path.exists()).is_false()
