"""
Test case: Symbolic link inside source directory pointing outside source
(error condition)

This test verifies that poexy-core correctly rejects a symbolic link located inside
the source directory that points to a target outside the source directory but within
the project root, as this represents an invalid configuration that should not be
allowed.

Test scenario:
- A symlink exists inside the source directory (e.g., "src/")
- The symlink target is outside the source directory but within the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- The system raises an appropriate error when detecting this invalid symlink
  configuration
- The build process is halted to prevent unpredictable or unsafe behavior
- Clear error messaging indicates the problematic symlink and its target

Edge case significance:
Prevents potentially dangerous or confusing symlink configurations where source content
attempts to reference content outside the source tree, ensuring clean separation of
concerns and predictable build behavior within the source directory boundaries.
"""
