"""
Test case: Multi-hop non-cyclical symlink chain resolves to a directory

This test ensures that poexy-core correctly resolves a multi-hop chain of
symlinks (a -> b -> c -> ...) that terminates at a directory within the
project, without cycles.

Test scenario:
- The source directory contains a short chain of symlinks that ultimately
  resolves to a directory inside the project root
- No cycles and the chain length is reasonable (well below max steps)

Expected behavior:
- The chain is resolved hop-by-hop to its directory target
- The build proceeds successfully according to policy
- No cycle-related or max-step errors are raised

Edge case significance:
Complements the multi-hop-to-file test by covering directory targets, ensuring
consistent handling across target types.
"""
