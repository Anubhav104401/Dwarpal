---
fingerprint: 2273758267da96e5
---
An `__init__.py` file turns a folder into a Python **package**: a folder of modules that can be imported as one unit, as in `import dwarpal_api`. Whatever is written in it runs the first time the package is imported.

@@ 1
The package's **docstring** — a one-sentence description of what it will contain. In Phase 0 the package is a skeleton: this line marks the folder as a package and records its purpose. Tools such as `help(dwarpal_api)` and code editors show this text. The real modules (`main.py`, `settings.py`, `modules/…`) arrive in Phase 1, following the layout in Stage 3 §3.1.
