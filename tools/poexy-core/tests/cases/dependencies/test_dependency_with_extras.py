"""
Test case: Dependencies with extra requirements specification

This test verifies that poexy-core correctly handles dependencies that include
extra requirements (optional dependencies). Extras allow packages to specify
additional features with their own dependency sets.

Test scenario:
- A project specifies dependencies with extras notation (e.g., "requests[security]")
- The build system processes these dependencies for package creation
- Extra requirements should be properly parsed and included in metadata
- Binary builds should handle extra dependencies correctly during installation

Expected behavior:
- Extra dependency syntax is parsed correctly from configuration
- Package metadata includes proper extra requirements specification
- Binary packages install extra dependencies when building executables
- Dependency resolution includes all required extras during builds

Edge case significance:
This tests extra dependency handling which is important for packages that
have optional features. Extras allow fine-grained dependency control and
feature sets. Proper handling ensures that optional dependencies are correctly
included when requested and that packages work with complex dependency graphs.
"""

# Test implementation will be added here
