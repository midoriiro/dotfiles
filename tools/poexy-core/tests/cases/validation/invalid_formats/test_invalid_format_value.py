"""
Test case: Invalid format value in wheel or package configuration

This test verifies that poexy-core properly handles and reports errors when an
invalid format value is specified in [tool.poexy.wheel.format] or related
configuration sections. Only predefined format values should be accepted.

Test scenario:
- A pyproject.toml file specifies an unrecognized format value
- The configuration validation attempts to parse the format setting
- An appropriate error should be raised listing valid format options
- The build process should fail with clear guidance on correct values

Expected behavior:
- A ValueError or configuration error is raised during validation
- The error message lists all valid format options (source, binary, etc.)
- Invalid format values are clearly identified in the error message
- Configuration validation occurs before any build processing starts

Edge case significance:
This tests configuration validation for format specifications. Format values
control the type of packages created and must be from a predefined set.
Proper validation prevents builds with undefined or unsupported formats.
"""

# Test implementation will be added here
