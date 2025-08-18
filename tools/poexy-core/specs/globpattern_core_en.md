# Glob Core (POSIX + Globstar)

## 1) Scope

* Applies to **relative paths** from a given root.
* Cross-platform: `/` and `\` are separators, **never** matched by `?`, `*` or `[...]`.
* The pattern **covers the entire path** (anchored start→end).

## 2) Recognized operators

* `?` → **exactly 1 character** in a segment (excluding separator).
* `*` → **0 or more characters** in a segment (excluding separator).
* `**` (special segment) → **0 or more complete segments** (can traverse directories).

  * Always used as a **complete segment** (`**/foo`, `src/**/bar`).
  * Forbidden inside a segment (e.g. `a**b` → error).
* `[...]` → **character class** (exactly 1 character):

  * **List**: `[abc]` → one of `a`/`b`/`c`
  * **Range**: `[a-z]`
  * **POSIX class**: `[[:digit:]]`, `[[:alpha:]]`, etc.
  * **Negation**: `[!abc]`, `[!a-z]`, `[![:space:]]`
    (`!` must be the 1st character after `[` to negate)

> **Dotfiles**: `*` and `?` do not match a `.` at the beginning of a segment. To match a dotfile, use a pattern starting explicitly with `.` (`.*`).

## 3) Escaping

* `[*]` → a literal `*`.
* `[?]` → a literal `?`.
* `[]]` → a class containing only `]`.
* `[!]]` → everything except `]`.
* `[-abc]` or `[abc-]` → includes a literal dash.
* Outside classes: backslash `\` can be used for escaping (`\*`, `\?`, `\[`) but depends on the shell/caller.

## 5) Error rules

* `**` inside a segment → error (`a**b`).
* `[` without `]` → error.
* Empty class `[]` → error.
* Lone `\` at the end → error.
* Empty pattern → only matches the empty string.

## 6) Canonical examples

### Match

* `*` → `a`, `abc`, `file.txt` (not `foo/bar`)
* `?at` → `Cat`, `bat`, `1at` (not `at`)
* `Letter[0-9]` → `Letter0` … `Letter9`
* `data.[!0-9]` → `data.a`, `data.X` (not `data.3`)
* `.*` → `.gitignore`, `.bashrc`
* `src/**/foo.py` → `src/foo.py`, `src/lib/foo.py`, `src/lib/test/foo.py`
* `**/*.c` → all `.c` files at any depth

---