"""
Test case: C source file (.c) inclusion in sdist packages

This test verifies that poexy-core correctly handles and includes C source files
(.c extension) in sdist packages. C source files are commonly included in source
distributions to allow compilation on target systems.

Test scenario:
- A project contains C source code files with .c extension
- The C files should be included in sdist packages for source distribution
- The source files should maintain their content and encoding
- Wheel builds may or may not include C files depending on configuration

Expected behavior:
- The .c file is properly detected and included in the sdist
- Source code content and line endings are preserved exactly
- File encoding (typically UTF-8) is maintained correctly
- Build systems can access and compile the C source after extraction

Edge case significance:
This tests source file preservation for C extensions that need compilation
on the target system. Proper C source handling is essential for packages
that provide both source and binary distributions of native extensions.
"""

# Test implementation will be added here
