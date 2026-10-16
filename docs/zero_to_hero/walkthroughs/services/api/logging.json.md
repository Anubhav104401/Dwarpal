---
fingerprint: f27f7017a1d1d654
---
The API's **logging configuration**: which log lines are kept, what they look like, and where they go. Uvicorn, the server program (§4.8), reads it at start-up:

```
uvicorn dwarpal_api.main:create_app --factory --port 8000 --log-config services/api/logging.json
```

Why a separate file instead of code? Where logs go is a decision for whoever *runs* the service, not for the code itself. In production the lines go to the screen of the container, and the platform collects them from there. The tests don't load this file at all, so they stay quiet.

The format is Python's standard **dictConfig** schema: a nested dict, written here as JSON.

@@ 1
The opening brace of the JSON object.

@@ 2
`"version": 1` — the schema version. It is required, and 1 is the only version that exists.

@@ 3
`"disable_existing_loggers": false` — keep loggers that were created before this configuration was loaded. The default, `true`, would silence them, a classic surprise.

@@ 4-6
**Formatters** — what a line looks like. There is one, named `json`. The special key `"()"` means "build it by calling this", followed by the full import path of our class: `JsonFormatter` in `dwarpal_api/logs.py`.

@@ 7-9
**Handlers** — where lines go. There is one, named `stdout`: Python's `StreamHandler`, writing with the `json` formatter to the program's **standard output**. `ext://sys.stdout` means "the Python object `sys.stdout`", the normal text output of a program.

!!! why "Why standard output?"
    A program that writes its own log files must also rotate them, clean them up and keep the disk from filling. A program that writes to standard output leaves all that to the platform running it — Docker in our case. This is one of the "12-factor app" principles (Stage 4 §9).

@@ 10
**Loggers** — the named sources of lines, and the rules for each.

@@ 11
`dwarpal` — our own code. Every logger whose name starts with `dwarpal.`, such as `dwarpal.api`, belongs to this family. Lines at level `INFO` and above go to `stdout`. `"propagate": false` stops each line from also being passed up to the root logger, which would print it a second time.

@@ 12
`uvicorn` — the server's own messages, such as "Application startup complete", in the same JSON format.

@@ 13
`uvicorn.access` — the server's own **access log**, one line per request, is switched off: no handlers, and only warnings would pass. Our own request log (`http/problems.py`) replaces it. Uvicorn's version includes the visitor's network address and the full address including any query string; ours records only what is needed.

@@ 14-15
The closing braces.
