"""
Test case: Constructing SymbolicLink on a non-symlink path raises

This test verifies that creating a `SymbolicLink` instance with a path that is
not a symbolic link immediately fails with `NotSymlinkError`.

Test scenario:
- Attempt to instantiate `SymbolicLink` with a regular file path
- Attempt to instantiate `SymbolicLink` with a directory path

Expected behavior:
- `NotSymlinkError` is raised for both cases, preventing misuse of the
  `SymbolicLink` API

Edge case significance:
Ensures clear guardrails on the API surface so that only true symlink paths are
accepted, reducing accidental misuse and improving error messages.
"""

from pathlib import Path

import pytest

from poexy_core.utils.symbolic_link import NotSymlinkError, SymbolicLink


@pytest.mark.parametrize("path", ["file", "directory/"])
@pytest.mark.prevent_venv_use
def test_symbolic_link_not_symlink_raises(tmp_path, path):
    is_directory = path.endswith("/")
    full_path = tmp_path / path
    if is_directory:
        full_path.mkdir()
    else:
        full_path.touch()

    with pytest.raises(
        NotSymlinkError,
        match="Not a symbolic link",
    ):
        SymbolicLink(full_path, Path.cwd())
