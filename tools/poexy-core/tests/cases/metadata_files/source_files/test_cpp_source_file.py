"""
Test case: C++ source file (.cpp) inclusion in sdist packages

This test verifies that poexy-core correctly handles and includes C++ source files
(.cpp extension) in sdist packages. C++ source files are included in source
distributions to enable compilation with C++ compilers on target systems.

Test scenario:
- A project contains C++ source code files with .cpp extension
- The C++ files should be included in sdist packages for source distribution
- The source files should preserve C++ syntax and formatting
- Build systems should be able to compile the C++ code after extraction

Expected behavior:
- The .cpp file is properly detected and included in the sdist
- C++ source code and syntax highlighting markers are preserved
- File encoding and special characters in comments are maintained
- C++ specific build requirements are properly handled

Edge case significance:
This ensures C++ extension support in Python packages. C++ files often contain
more complex syntax and build requirements than C files. Proper handling
enables object-oriented and template-based native extensions.
"""

# Test implementation will be added here
