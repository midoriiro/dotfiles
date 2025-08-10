"""
Test case: Invalid or non-existent source path in package configuration

This test verifies that poexy-core properly handles and reports errors when the
source path specified in [tool.poexy.package.{name}.source] points to a location
that does not exist or is not accessible.

Test scenario:
- A pyproject.toml file specifies a source path that does not exist
- The build system attempts to locate the source directory
- An appropriate error should be raised with clear messaging
- The build process should fail gracefully without creating partial artifacts

Expected behavior:
- A ValueError or PyProjectError is raised with descriptive message
- The error message clearly indicates which source path is invalid
- No partial packages or temporary files are left behind
- The error occurs early in the build process before extensive processing

Edge case significance:
This tests error handling for one of the most common configuration mistakes.
Invalid source paths can occur due to typos, directory restructuring, or
misconfigured build environments. Proper error reporting helps developers
quickly identify and fix configuration issues.
"""

# Test implementation will be added here
