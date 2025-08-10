"""
Test case: Symbolic link with absolute target inside the project (file)

This test ensures that poexy-core correctly handles a symbolic link whose
target is specified as an absolute path that still resides within the project
root and points to a regular file.

Test scenario:
- A symlink in the source directory points, via an ABSOLUTE path, to a file
  located inside the project root
- The build system encounters this symlink during file discovery

Expected behavior:
- The symlink resolution recognizes that the absolute target remains under the
  project base path (no escape)
- The build proceeds successfully according to policy (follow/preserve/resolve)
- Package integrity is maintained

Edge case significance:
Verifies that absolute-path symlinks are not treated as escapes when they
remain inside the project, avoiding false positives and ensuring predictable
builds under varied filesystem layouts.
"""
