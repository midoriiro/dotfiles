"""
Test case: Symbolic link breaking into source directory from outside (error condition)

This test verifies that poexy-core correctly rejects a symbolic link located outside
the source directory that breaks into the source directory by pointing to content
within the source tree, as this represents an invalid configuration that violates
source directory boundaries.

Test scenario:
- A symlink exists outside the source directory (e.g., in project root)
- The symlink target breaks into the source directory, pointing to a location
  within the source tree (e.g., "src/")
- The build system encounters this boundary-breaking symlink during file discovery

Expected behavior:
- The system raises an appropriate error when detecting this boundary violation
- The build process is halted to prevent external access into the source tree
- Clear error messaging indicates the problematic symlink and its intrusive target

Edge case significance:
Enforces strict source directory boundaries by preventing external symlinks from
breaking into the designated source tree, ensuring secure and predictable
build behavior while maintaining clear separation between source and non-source content.
"""
