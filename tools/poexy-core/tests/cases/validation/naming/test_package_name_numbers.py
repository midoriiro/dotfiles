"""
Test case: Package name containing numbers

This test verifies that poexy-core correctly handles package names that contain
numeric characters, which are valid in Python package names. Numbers can appear
anywhere in package names and should be preserved during processing.

Test scenario:
- A project has a package name containing numbers (e.g., "package123", "py2to3")
- The build system processes the numeric package name
- Number characters should be preserved in all package metadata
- Numeric package names should work with all package formats

Expected behavior:
- Numeric characters in package names are preserved exactly
- Package name validation accepts valid numeric combinations
- Wheel and sdist metadata correctly include numeric characters
- Import statements work with numeric package names

Edge case significance:
This tests numeric character handling in package names. Numbers are commonly
used in package names for versioning schemes, compatibility indicators, or
technical specifications. Proper handling ensures these packages can be
created, distributed, and imported successfully.
"""

# Test implementation will be added here
