---
fingerprint: edeea4716450b135
---
`book.toml` holds the book's **settings**. Keeping settings in a separate file, rather than inside `build.py`, means you can add a chapter or change the title **without touching any program code**. "Separate the *what* from the *how*" is one of the oldest good habits in software.

The file is written in **TOML** ("Tom's Obvious, Minimal Language"):

- `name = value` sets a value;
- text goes in double quotes;
- lists go in square brackets;
- a line like `[coverage]` starts a named group of settings, which TOML calls a **table**.

Python reads TOML with its built-in `tomllib`.

!!! alt "Alternatives considered"
    - **JSON** doesn't allow comments and is fussy about commas.
    - **YAML** has surprising rules: the unquoted word `no` can turn into *false*.

    TOML is what Python's own packaging uses (`pyproject.toml`), so it is the natural choice for a Python tool.

@@ 1
`title = "Dwarpal — Zero to Hero"` is the book's title, shown in the browser tab and the sidebar. The `—` survives because every file is read and written as UTF-8 (§0.2).

@@ 2
`subtitle = …` is a one-line description, printed in the footer.

@@ 3
`output = "zero_to_hero.html"` is the name of the file `build.py` creates, next to `build.py` in `docs/zero_to_hero/`, as the project owner asked.

@@ 4
`abbreviations = "abbreviations.md"` is the file of hover definitions, which is attached to every chapter and walkthrough note when it is converted.

@@ 5-23
`chapters = [ … ]` is the **reading order** of the book. Each line inside the brackets is one chapter file, and the order here is the order in the book. The numbers at the start of the file names only keep the folder tidy.

The list grows as the project does:

- Phase 0 added Part 4 (the tools) and Part 5 (building it, file by file);
- Phase 1 added `07_part5_phase1.md`, the walking skeleton's chapter. Each phase gets its own chapter file, so no single file grows unmanageably long.

!!! try "Try it yourself"
    Move the `99_glossary.md` line to the top and run `uv run tasks.py book`: the glossary becomes the first chapter. Move it back afterwards.

Phase 3 added `09_part5_phase3.md`: liveness and anti-spoofing (§5.3).

Phase 4 added `10_part5_phase4.md`: the platform (§5.4).

Phases 6 and 7 began out of order (some of their work needs nothing waiting for approval): `12_part5_phase6.md` (step-up verifiers, §5.6) and `13_part5_phase7.md` (hardening, §5.7). The number 11 is kept free for Phase 5, so the files stay in the book's reading order.

And `11_part5_phase5.md` (front-end excellence, §5.5), in the place kept for it.

@@ 25
`[coverage]` starts the group of settings for the **coverage check** — which project files must have a line-by-line explanation. In Python this group is read as `config["coverage"]`.

@@ 26-31
`include = [ … ]` lists **glob patterns** for files that count as code. In a glob, `*` means "any characters within one name", and `**` means "any number of folders, including none". The patterns cover:

- Python (`.py`);
- TypeScript and JavaScript (`.ts`, `.tsx`, `.js`, `.mjs`);
- styles (`.css`) and web pages (`.html`);
- settings files (`.toml`, `.yaml`, `.yml`, `.json`);
- database scripts (`.sql`) and shell scripts (`.sh`, `.ps1`);
- text lists (`.txt`);
- special files without extensions: `Dockerfile`, `Caddyfile`, `.env.example`;
- four "dotfiles" that change how tools treat the whole project — `.gitignore`, `.gitattributes`, `.editorconfig`, `.python-version` (added in Phase 0);
- **Mako templates** (`.mako`, added in Phase 1). Alembic uses one as the blueprint for every new database migration (§4.10). A file that shapes other code is code too, so it gets explained.

Markdown (`.md`) is deliberately not included: it is prose, not code.

@@ 32
`exclude = [ … ]` lists patterns that are removed even if they matched `include`:

- the generated book itself — explaining the explainer's output would loop forever;
- **lockfiles** (`pnpm-lock.yaml`, `package-lock.json`, `uv.lock`) — thousands of machine-written lines. §0.17 explains what they are instead;
- `next-env.d.ts` — a file Next.js writes for itself into each web app, and which is never committed (added in Phase 1, see `.gitignore`).

`apps/web/public/mediapipe/**` (added in Phase 3) — MediaPipe's WebAssembly loaders, copied in before each build: tens of thousands of lines of someone else's generated code.

`docs/api/openapi.json` (Phase 4) — the API's published OpenAPI document: almost 5,000 lines that `cli openapi` writes from the code itself. The code that produces it is explained line by line instead (`http/problems.py`, `cli.py`), and a test fails if the file and the code ever disagree.

@@ 33-37
`prune = [ … ]` lists **folder names the scanner never enters**, because they hold things we didn't write:

- Git's own history (`.git`);
- installed libraries (`.venv`, `node_modules`);
- tool caches (`__pycache__`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, and Hypothesis's `.hypothesis`);
- build outputs (`.next`, `.turbo`, `dist`);
- downloaded training data (`.datasets`);
- training runs and experiment logs (`.runs`, `mlruns`);
- the builder's own snapshots (`.snapshots`) — copies of code, which would otherwise be counted twice;
- local AI-assistant settings (`.claude`), which are not part of the project and are never committed (see `.gitignore`);
- the end-to-end tests' results (`test-results`, `playwright-report`), recreated on every run (added in Phase 1), and Lighthouse CI's scratch folder (`.lighthouseci`, Phase 5).

!!! warn "Careful — a loophole we closed"
    An earlier version also pruned folders called `data` and `build`. That was a hidden loophole: a real code folder named, say, `ml/data/` would silently escape the check. Only names that are *always* generated or downloaded are pruned. That is also why the training data folder is deliberately called `.datasets`.
