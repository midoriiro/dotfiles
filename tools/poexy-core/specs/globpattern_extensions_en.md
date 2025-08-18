# Glob Extensions (beyond core)

These rules extend the **glob core** (POSIX + globstar `**`).
Everything not listed here is already covered by the core.

---

## 1) Alternatives

### 1.1 Entire segment

* `{seg1|seg2|…}` : alternative **at segment level** (one choice entry).
* Literal exclusion in `{}` : `!name` = "any segment **different from** `name`".
  *Example* : `{foo|!bar}` → `foo` or anything except `bar`.
* Each entry can contain `[]` and/or `()` (see below).

### 1.2 Sub-segment (text)

* `(alt1|alt2|…)` : **textual** alternative *within* a segment.

  * Content : text and `[]` classes allowed.
  * No `*`, `**`, `{}`, or nested `()`.
  * *Examples* : `file.(py|pyi)`, `LICEN(SE|CE)`.

---

## 2) Character classes (extensions)

* **Dedicated quantifier** on a class : `[]#n` with `n ≥ 2`.
  *Examples* :

  * `[0-9]#2` → two digits.
  * `[A-F0-9]#3` → three characters from the class.

> The quantifier only applies **to `[]` classes** (not to `{}`, `()`, or literals).

---

## 3) Composition & restrictions

* Within a segment, you can combine :
  literals → `[]` classes (then `#n`) → `()` alternatives → `?` and `*` wildcards.
* No nested `{}` in `{}`, nor `()` in `()`.
* `[]` and/or `()` can appear in a `{…}` entry.
* `[]` can appear in a `(…)` entry.
* `**` remains reserved as entire segment (no mixing with text in the same segment).

---

## 4) Type anchors (final segment only)

* Types : `:file`, `:dir`, `:link`.
* Position : only at the **end of the last segment**.
* Forbidden on `**`.

### Rules :

* `:file` / `:link` → last segment must be **explicit** or `{…}` of explicits.

  * Valid : `**/README:file`, `**/{seg1|seg2}:file`, `**/v[0-9]#2:link`.
  * Invalid : `**/**:file`.

* `:dir` → last segment must be `*`, literal or `{…}` of explicits.

  * Valid : `**/*:dir`, `**/{img|images}:dir`, `**/images:dir`.
  * Invalid : `**:dir`

---

## 5) Global negation

* A pattern can be preceded by `!` → exclude matches (last match wins, `.gitignore` style).
  *Example* : `**/*.py`, then `!**/test_*.py`.

---

## 6) Error rules (extension specific)

* Unclosed `{}` or `()` → error.
* `()` containing `{}`, or nested `()` → error.
* `[]` containing `{}`, or nested `()` → error.
* `{}` containing nested `{}` → error.
* `[]#n` with `n < 2` → error.
* Anchor on intermediate segment → error.
* Anchor on `**` → error.

---

## 7) Canonical examples

* `**/README:file` → `README` files at any depth.
* `**/{LICENSE|LICEN(SE|CE)}:file` → `LICENSE`, `LICENCE`.
* `assets/[0-9]#3.(png|jpg):file` → `assets/123.png`, `assets/456.jpg`.
* `**/*:dir` → all directories.
* `**/{img|images}:dir` → `img` or `images` directories.
* `docs/v[0-9]#2` → `v01`, `v12`…
* `**/*.py` + `!**/test_*.py` → all `.py` except `test_*.py`.

---

👉 Here we have :

* **core** = POSIX + globstar.
* **extensions** = `{}`, `()`, `[]#n`, `:file/:dir/:link` anchors, global negation `!pattern`, strict usage rules.
