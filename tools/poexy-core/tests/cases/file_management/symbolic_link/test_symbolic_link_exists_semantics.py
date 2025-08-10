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
