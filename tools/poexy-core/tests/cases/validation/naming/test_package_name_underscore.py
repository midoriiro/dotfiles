"""
Test case: Package name containing underscores

This test verifies that poexy-core correctly handles package names that contain
underscores, which are valid in Python package names and commonly used for
module naming. Underscores have different normalization rules than hyphens.

Test scenario:
- A project has a package name containing underscores (e.g., "my_package")
- The build system processes the package name for distribution
- Package name handling should preserve or normalize underscores appropriately
- Import names and distribution names should be handled correctly

Expected behavior:
- Underscore package names are accepted and processed correctly
- Package name normalization follows Python naming conventions
- Distinction between distribution name and import name is maintained
- Wheel and sdist metadata reflect proper naming conventions

Edge case significance:
This tests underscore handling in package names, which differs from hyphen
normalization. Underscores are often preserved in import names while
distribution names may use different conventions. Proper handling ensures
packages can be both distributed and imported correctly.
"""

# Test implementation will be added here
