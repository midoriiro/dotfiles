"""
Test case: Multi-hop non-cyclical symlink chain resolves to a regular file

This test ensures that poexy-core correctly resolves a multi-hop chain of
symlinks (a -> b -> c -> ...) that terminates at a regular file within the
project, without cycles.

Test scenario:
- The source directory contains a short chain of symlinks that ultimately
  resolves to a regular file inside the project root
- No cycles and the chain length is reasonable (well below max steps)

Expected behavior:
- The chain is resolved hop-by-hop to its file target
- The build proceeds successfully according to policy
- No cycle-related or max-step errors are raised

Edge case significance:
Validates that ordinary multi-hop symlink chains (non-cyclical) are handled
gracefully and do not cause false error conditions.
"""
