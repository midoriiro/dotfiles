"""
Test case: Multiple license files specified in project metadata

This test verifies that poexy-core correctly handles projects that specify
multiple license files in their metadata. Some projects use multiple licenses
or have complex licensing arrangements requiring multiple license files.

Test scenario:
- A project specifies multiple license files in the license-files field
- Each license file exists and contains valid license content
- The build system should include all specified license files in packages
- Package metadata should reference all license files appropriately

Expected behavior:
- All specified license files are included in both wheel and sdist packages
- License file paths are validated and resolved correctly
- Package metadata correctly references multiple license files
- License file content is preserved exactly during packaging

Edge case significance:
This tests multi-license support which is important for complex projects
that use multiple licenses or include third-party code with different licenses.
Proper handling ensures legal compliance and complete license information
distribution. Multiple license support is required for many open source projects.
"""

# Test implementation will be added here
