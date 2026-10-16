---
fingerprint: 7f76d00f9f0589b9
---
`biome.json` configures **Biome**, the formatter and linter for the JavaScript, TypeScript, JSON and CSS side of the project — the counterpart of Ruff on the Python side (§4.4).

@@ 1
`{` — start of the JSON object.

@@ 2
`"$schema"` — the JSON Schema for exactly this Biome version (2.5.15), for editor autocompletion and validation.

@@ 3-7
`"vcs"` — integration with the **version control system**:

- `"enabled": true` — switch it on;
- `"clientKind": "git"` — the project uses Git;
- `"useIgnoreFile": true` — skip every path listed in `.gitignore`.

So Biome never wastes time formatting `node_modules` or build outputs, and the list of ignored paths lives in one place only.

@@ 8-10
`"files"` → `"includes"` — which files Biome should look at. `"**"` means everything; entries starting with `!` are exclusions:

- `!docs/zero_to_hero/**/*.html` — the book's HTML: the generated book itself, and its hand-tuned template, whose exact layout the book explains line by line;
- `!docs/zero_to_hero/.snapshots` — the builder's snapshot copies (§X.6).

@@ 11-16
`"formatter"`:

- `"enabled": true` — switch on formatting;
- `"indentStyle": "space"` — indent with spaces, never tabs;
- `"indentWidth": 2` — two spaces per level, matching `.editorconfig` (§5.0.1);
- `"lineWidth": 110` — wrap lines longer than 110 characters.

@@ 17-22
`"linter"`: switch it on, and use Biome's **recommended** set of rules — the rules its authors consider safe and valuable for nearly every project.

The setting is written `"preset": "recommended"`. The first version said `"recommended": true`, but Biome 2.5 reported that form as deprecated, and `biome migrate --write` rewrote it automatically (§4.4).

@@ 23-27
`"css"` → `"parser"` → `"tailwindDirectives": true` (added in Phase 1) — let Biome read the special instructions that **Tailwind CSS** adds to stylesheets, such as `@theme` (§4.18). Without this, Biome stopped at the first one with "Tailwind-specific syntax is disabled", and couldn't check or format the web apps' styles at all.

@@ 28-33
`"javascript"` → `"formatter"`:

- `"quoteStyle": "double"` — use `"double quotes"` for strings. It matches JSON (which only allows double quotes) and our Python style.
- `"semicolons": "always"` — end statements with `;`. JavaScript can usually guess where a statement ends, but in a few rare situations it guesses wrong. Writing every semicolon removes those surprises.

@@ 34-40
`"assist"` → `"actions"` → `"source"` → `"organizeImports": "on"` — keep `import` lines sorted and grouped automatically, the same job Ruff's `I` rules do for Python.

@@ 41
`}` — the end of the file.
