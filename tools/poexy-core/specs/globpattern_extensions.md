# Glob Extensions (au-delà du core)

Ces règles s’ajoutent au **glob core** (POSIX + globstar `**`).
Tout ce qui n’est pas listé ici est déjà couvert par le core.

---

## 1) Alternatives

### 1.1 Segment entier

* `{seg1|seg2|…}` : alternative **au niveau segment** (une entrée au choix).
* Exclusion littérale dans `{}` : `!name` = « tout segment **différent de** `name` ».
  *Exemple* : `{foo|!bar}` → `foo` ou n’importe quoi sauf `bar`.
* Chaque entrée peut contenir `[]` et/ou `()` (voir plus bas).

### 1.2 Sous-segment (texte)

* `(alt1|alt2|…)` : alternative **textuelle** *dans* un segment.

  * Contenu : texte et classes `[]` autorisées.
  * Pas de `*`, `**`, `{}`, ni de `()` imbriqués.
  * *Exemples* : `file.(py|pyi)`, `LICEN(SE|CE)`.

---

## 2) Classes de caractères (extensions)

* **Quantificateur dédié** sur une classe : `[]#n` avec `n ≥ 2`.
  *Exemples* :

  * `[0-9]#2` → deux chiffres.
  * `[A-F0-9]#3` → trois caractères de la classe.

> Le quantificateur ne s’applique **qu’aux classes `[]`** (pas à `{}`, `()`, ni aux littéraux).

---

## 3) Composition & restrictions

* À l’intérieur d’un segment, on peut combiner :
  littéraux → classes `[]` (puis `#n`) → alternatives `()` → jokers `?` et `*`.
* Pas d’imbrication `{}` dans `{}`, ni `()` dans `()`.
* `[]` et/ou `()` peuvent apparaître dans une entrée de `{…}`.
* `[]` peut apparaître dans une entrée de `(…)`.
* `**` reste réservé comme segment entier (pas de mélange avec du texte dans le même segment).

---

## 4) Ancres de type (segment final uniquement)

* Types : `:file`, `:dir`, `:link`.
* Position : uniquement à la **fin du dernier segment**.
* Interdit sur `**`.

### Règles :

* `:file` / `:link` → dernier segment doit être **explicite** ou `{…}` d’explicites.

  * Valides : `**/README:file`, `**/{seg1|seg2}:file`, `**/v[0-9]#2:link`.
  * Invalides : `**/**:file`.

* `:dir` → dernier segment doit être `*`, litéral ou `{…}` d’explicites.

  * Valides : `**/*:dir`, `**/{img|images}:dir`, `**/images:dir`.
  * Invalides : `**:dir`

---

## 5) Négation globale

* Un motif peut être précédé de `!` → exclure les correspondances (dernier match gagne, style `.gitignore`).
  *Exemple* : `**/*.py`, puis `!**/test_*.py`.

---

## 6) Règles d’erreur (spécifiques extensions)

* `{}` ou `()` non fermés → erreur.
* `()` contenant, `{}`, ou `()` imbriqués → erreur.
* `[]` contenant, `{}`, ou `()` imbriqués → erreur.
* `{}` contenant, `{}` imbriqués → erreur.
* `[]#n` avec `n < 2` → erreur.
* Ancre sur segment intermédiaire → erreur.
* Ancre sur `**` → erreur.

---

## 7) Exemples canoniques

* `**/README:file` → fichiers `README` à n’importe quelle profondeur.
* `**/{LICENSE|LICEN(SE|CE)}:file` → `LICENSE`, `LICENCE`.
* `assets/[0-9]#3.(png|jpg):file` → `assets/123.png`, `assets/456.jpg`.
* `**/*:dir` → tous les dossiers.
* `**/{img|images}:dir` → dossiers `img` ou `images`.
* `docs/v[0-9]#2` → `v01`, `v12`…
* `**/*.py` + `!**/test_*.py` → tous les `.py` sauf `test_*.py`.

---

👉 Là on a bien :

* **core** = POSIX + globstar.
* **extensions** = `{}`, `()`, `[]#n`, ancres `:file/:dir/:link`, négation globale `!pattern`, règles strictes d’usage.
