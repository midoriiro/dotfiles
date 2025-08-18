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

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "resources/a.txt:purelib",
    "resources/b.txt:purelib",
    "resources/c.txt:purelib",
    "resources/nested/a_deep.txt:purelib",
    "resources/nested/b_deep.txt:purelib",
    "resources/nested/deeper/a_very_deep.txt:purelib",
    "resources/images/icon1.png:purelib",
    "resources/images/icon2.png:purelib",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(SamplePaths.FileManagementInclusions / "nested_patterns")


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
