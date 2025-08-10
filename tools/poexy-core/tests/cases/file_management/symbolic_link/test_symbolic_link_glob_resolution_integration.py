"""
Test case: Glob resolution integration with symlinks

This test verifies that when package files are selected via glob patterns, any
matched symbolic links are subject to the same validations as direct paths:
broken-link detection, escape prevention, and accessibility checks.

Test scenario:
- A glob pattern matches one or more symlinks in the source directory
- Targets include a valid in-project file/dir and at least one invalid case
  (broken, escaping, or unreadable)

Expected behavior:
- For valid targets, the files/directories are included as expected
- For invalid targets, appropriate errors are raised (`BrokenSymlinkError`,
  `SymlinkEscapingError`, or `SymlinkNotAccessibleError`)
- The resolution process mirrors the logic used for direct path selection

Edge case significance:
Ensures consistent behavior between explicit path selection and glob-driven
selection, preventing blind spots when patterns capture symbolic links.
"""
