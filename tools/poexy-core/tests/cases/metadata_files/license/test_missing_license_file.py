"""
Test case: Missing license file specified in project metadata

This test verifies that poexy-core properly handles and reports errors when a
license file is specified in the project metadata but the file does not exist
on the filesystem. License files are important for legal compliance.

Test scenario:
- A pyproject.toml file specifies a license file in project metadata
- The specified license file does not exist at the given location
- The build system attempts to include the license in the package
- An appropriate error should be raised about the missing license file

Expected behavior:
- A FileNotFoundError is raised when the license file cannot be found
- The error message clearly identifies the missing license file path
- The error occurs during metadata processing or file collection
- License file validation happens early in the build process

Edge case significance:
This tests license file validation which is crucial for legal compliance.
Missing license files can cause legal issues for distributed packages.
Proper validation ensures that license information is correctly included
in all package distributions and prevents accidental omission.
"""

# Test implementation will be added here
