"""
Test case: Symbolic link with absolute target inside the project (directory)

This test ensures that poexy-core correctly handles a symbolic link whose
target is specified as an absolute path within the project root and points to a
directory.

Test scenario:
- A symlink in the source directory points, via an ABSOLUTE path, to a
  directory located inside the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- The absolute target is recognized as remaining under the project base path
  (no escape)
- The build proceeds successfully (follow/preserve/resolve according to
  policy)
- Package integrity is maintained

Edge case significance:
Ensures consistent handling for absolute-path directory targets that are inside
the project, preventing unnecessary rejections while maintaining security.
"""
