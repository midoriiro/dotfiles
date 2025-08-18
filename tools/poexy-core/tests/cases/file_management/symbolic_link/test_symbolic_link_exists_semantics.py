"""
Test case: SymbolicLink.exists semantics

This test documents the semantics of `SymbolicLink.exists(path)` and ensures it
behaves consistently across various path types.

Test scenario:
- Check `SymbolicLink.exists` on an existing symlink to a valid target
- Check `SymbolicLink.exists` on a broken symlink
- Check `SymbolicLink.exists` on a regular file
- Check `SymbolicLink.exists` on a directory
- Check `SymbolicLink.exists` on a non-existent path

Expected behavior:
- Returns True for an existing symlink regardless of whether its target exists
- Returns False for regular files, directories, and missing paths

Edge case significance:
Clarifies the contract of `exists` to avoid confusion during file discovery and
to keep test expectations precise and repeatable.
"""

from pathlib import Path

import pytest
from assertpy import assert_that

from poexy_core.utils.symbolic_link import SymbolicLink


@pytest.mark.parametrize(
    "path, expected",
    [
        ("file", False),
        ("directory/", False),
        (">link", True),
        (">#broken-link", True),
        ("?not-exists", False),
    ],
)
@pytest.mark.prevent_venv_use
def test_symbolic_link_not_symlink_raises(tmp_path: Path, path: str, expected: bool):
    is_directory = path.endswith("/")
    is_link = path.startswith(">")
    is_broken_link = path.startswith(">#")
    is_not_exists = path.startswith("?")
    is_file = (
        not is_directory and not is_link and not is_broken_link and not is_not_exists
    )
    full_path = tmp_path / path
    if is_directory:
        full_path.mkdir()
    elif is_file:
        full_path.touch()
    elif is_link:
        path = path.replace(">", "")
        target = tmp_path / "target"
        target.touch()
        full_path = tmp_path / path
        full_path.symlink_to(tmp_path / "target")
    elif is_broken_link:
        path = path.replace(">#", "")
        full_path = tmp_path / path
        full_path.symlink_to(tmp_path / "target")
    elif is_not_exists:
        path = path.replace("?", "")
        full_path = tmp_path / path

    result = SymbolicLink.exists(full_path)
    assert_that(result).is_equal_to(expected)
