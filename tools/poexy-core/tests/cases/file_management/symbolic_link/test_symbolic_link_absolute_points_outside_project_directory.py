"""
Test case: Symbolic link with absolute target outside the project (directory)

This test verifies that poexy-core prevents unsafe traversal when a symbolic
link in the source directory points, via an ABSOLUTE path, to a directory
outside the project root.

Test scenario:
- A symlink in the source directory uses an absolute path to target a
  directory located outside the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- The symlink is detected as escaping the base path
- A `SymlinkEscapingError` is raised and the build is blocked
- Package integrity and security boundaries are upheld

Edge case significance:
Prevents directory traversal via absolute-path symlinks to outside locations,
ensuring the build remains confined to the intended project scope.
"""
