"""
Test case: Binary package with invalid or non-existent entry point specification

This test verifies that poexy-core correctly handles the case where a binary
entry point is explicitly specified in configuration but the referenced file
or function does not exist. This tests entry point validation.

Test scenario:
- A project explicitly specifies an entry point in binary configuration
- The specified entry point file or function does not exist
- The build system attempts to validate the entry point specification
- Appropriate error handling should occur for invalid entry point references

Expected behavior:
- Invalid entry point specifications are detected during validation
- Error messages clearly identify the missing or invalid entry point
- File existence and function accessibility are validated
- Build fails early when entry points cannot be resolved

Edge case significance:
This tests explicit entry point validation which is important for binary
packaging reliability. Invalid entry points can cause runtime failures
in generated executables. Proper validation ensures that entry points
are valid and accessible before binary creation begins.
"""

# Test implementation will be added here
