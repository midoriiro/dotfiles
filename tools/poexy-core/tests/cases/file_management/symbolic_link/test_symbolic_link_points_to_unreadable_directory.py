"""
Test case: Symbolic link pointing to an unreadable directory

This test verifies that poexy-core correctly handles a symbolic link whose
resolved target is a directory without sufficient read permissions.

Test scenario:
- A symlink exists in the source directory pointing (directly or via a chain)
  to a directory with no readable bits set
- The build system encounters this symlink during file discovery

Expected behavior:
- The system raises `SymlinkNotAccessibleError` when the target directory
  cannot be read due to insufficient permissions
- Package integrity and security boundaries are preserved without leaking
  restricted contents

Edge case significance:
Complements the unreadable-file test by covering unreadable directories,
ensuring consistent permission enforcement for both target types.
"""
