# Glob Core (POSIX + Globstar)

## 1) Portée

* S’applique à des **chemins relatifs** à une racine donnée.
* Multi-plateforme : `/` et `\` sont des séparateurs, **jamais** matchés par `?`, `*` ou `[...]`.
* Le motif **couvre tout le chemin** (ancrage début→fin).

## 2) Opérateurs reconnus

* `?` → **exactement 1 caractère** dans un segment (hors séparateur).
* `*` → **0 ou plus caractères** dans un segment (hors séparateur).
* `**` (segment spécial) → **0 ou plusieurs segments complets** (peut traverser des répertoires).

  * Toujours utilisé comme **segment entier** (`**/foo`, `src/**/bar`).
  * Interdit à l’intérieur d’un segment (ex. `a**b` → erreur).
* `[...]` → **classe de caractères** (exactement 1 caractère) :

  * **Liste** : `[abc]` → un de `a`/`b`/`c`
  * **Plage** : `[a-z]`
  * **Classe POSIX** : `[[:digit:]]`, `[[:alpha:]]`, etc.
  * **Négation** : `[!abc]`, `[!a-z]`, `[![:space:]]`
    (`!` doit être le 1er caractère après `[` pour nier)

> **Dotfiles** : `*` et `?` ne matchent pas un `.` en début de segment. Pour matcher un dotfile, utiliser un motif commençant explicitement par `.` (`.*`).

## 3) Échappement

* `[*]` → un `*` littéral.
* `[?]` → un `?` littéral.
* `[]]` → une classe contenant uniquement `]`.
* `[!]]` → tout sauf `]`.
* `[-abc]` ou `[abc-]` → inclut un tiret littéral.
* Hors des classes : antislash `\` peut servir à échapper (`\*`, `\?`, `\[`) mais dépend du shell/appelant.

## 5) Règles d’erreur

* `**` dans un segment → erreur (`a**b`).
* `[` sans `]` → erreur.
* Classe vide `[]` → erreur.
* `\` final seul → erreur.
* Motif vide → ne matche que la chaîne vide.

## 6) Exemples canoniques

### Match

* `*` → `a`, `abc`, `file.txt` (pas `foo/bar`)
* `?at` → `Cat`, `bat`, `1at` (pas `at`)
* `Letter[0-9]` → `Letter0` … `Letter9`
* `data.[!0-9]` → `data.a`, `data.X` (pas `data.3`)
* `.*` → `.gitignore`, `.bashrc`
* `src/**/foo.py` → `src/foo.py`, `src/lib/foo.py`, `src/lib/test/foo.py`
* `**/*.c` → tous les fichiers `.c` à n’importe quelle profondeur

---