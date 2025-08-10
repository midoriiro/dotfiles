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
