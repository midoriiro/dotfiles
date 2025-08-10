"""
Test case: Local dependency with relative path reference

This test verifies that poexy-core correctly handles dependencies that are
specified as local packages using relative paths. Local dependencies are
commonly used for development of related packages or monorepo setups.

Test scenario:
- A project specifies a local dependency using a relative path (e.g., "../sibling-package")
- The build system processes the local dependency during package creation
- The dependency should be resolved relative to the project root
- Package builds should include the local dependency appropriately

Expected behavior:
- Relative path dependencies are resolved correctly from the project location
- Local package content is accessed and included in builds as appropriate
- Dependency resolution works consistently across different build environments
- Path resolution handles various relative path formats correctly

Edge case significance:
This tests local dependency handling which is important for development
workflows and monorepo structures. Relative path dependencies allow packages
to depend on local development versions without publishing. Proper handling
ensures that local dependencies work correctly during development and testing.
"""

# Test implementation will be added here
