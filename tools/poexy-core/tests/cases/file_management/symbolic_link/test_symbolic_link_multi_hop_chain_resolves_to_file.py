"""
Test case: Multi-hop non-cyclical symlink chain resolves to a regular file

This test ensures that poexy-core correctly resolves a multi-hop chain of
symlinks (a -> b -> c -> ...) that terminates at a regular file within the
project, without cycles.

Test scenario:
- The source directory contains a short chain of symlinks that ultimately
  resolves to a regular file inside the project root
- No cycles and the chain length is reasonable (well below max steps)

Expected behavior:
- The chain is resolved hop-by-hop to its file target
- The build proceeds successfully according to policy
- No cycle-related or max-step errors are raised

Edge case significance:
Validates that ordinary multi-hop symlink chains (non-cyclical) are handled
gracefully and do not cause false error conditions.
"""

import pytest

from tests.conftests.paths import SamplePaths
from tests.utils.asserts import AssertPaths
from tests.utils.paths import SymlinkMultiNodeHopPath

# pylint: disable=redefined-outer-name

expected_files = [
    "__init__.py",
    "!:symlink:ln",
    "!:target/not-included",
]


@pytest.fixture()
def project_path(sample_project):
    return sample_project(
        SamplePaths.FileManagementSymbolicLink
        / "symbolic_link_multi_hop_chain_resolves_to_file"
    )


@pytest.mark.file_operation(
    path=SymlinkMultiNodeHopPath("src/symlink", "src/target/not-included")
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


@pytest.mark.file_operation(
    path=SymlinkMultiNodeHopPath("src/symlink", "src/target/not-included")
)
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
