"""
Test case: Package name containing hyphens

This test verifies that poexy-core correctly handles package names that contain
hyphens, which are valid in Python package names according to PEP 508. Hyphens
are commonly used in package names but require proper normalization.

Test scenario:
- A project has a package name containing one or more hyphens (e.g., "my-package")
- The build system processes the package name for wheel and sdist creation
- Package name normalization should follow PEP standards
- Both wheel and sdist should handle hyphenated names correctly

Expected behavior:
- Hyphenated package names are accepted and processed correctly
- Package name normalization follows PEP 508 and PEP 427 standards
- Wheel metadata uses the normalized form of the package name
- Installation and import paths are handled appropriately

Edge case significance:
This tests package name normalization for hyphenated names, which are common
in the Python ecosystem. Proper handling ensures compatibility with PyPI
naming conventions and package managers. Hyphen normalization is critical
for package discovery and installation consistency.
"""

# Test implementation will be added here
