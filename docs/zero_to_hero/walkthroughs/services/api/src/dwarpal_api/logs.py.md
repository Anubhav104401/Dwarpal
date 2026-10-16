---
fingerprint: 290ce36d76325516
---
**Logs** are a program's diary: short lines written as it works, such as "request received, answered 201 in 12 ms". When something goes wrong at 3 a.m., the logs are how people find out what happened.

This file decides what one diary line looks like. Every line is one **JSON object** (§0.11). Here is a real one, wrapped onto two lines to fit the page:

```json
{"time": "2026-10-16T05:12:43.607+00:00", "level": "info", "logger": "dwarpal.api", "message": "request",
 "request_id": "req_0123456789abcdef", "method": "POST", "path": "/v1/verification-sessions", "status": 201, "duration_ms": 12.5}
```

Plain sentences are easy for people to read but hard for machines to search. JSON lines are still readable, and a log tool can answer questions such as "show every request slower than 500 ms" instantly. This style is called **structured logging**.

!!! key "What is never logged"
    Request bodies, headers, query strings, API keys, client secrets and pictures. A log line names *which* request it is about — never *what* was sent. A test in `test_api.py` checks that neither the API key nor the client secret ever appears in the logs.

@@ 1
The docstring: one JSON object per line, for machines and people alike.

@@ 3
The project-wide type-hint setting.

@@ 5-7
Three modules from Python's standard library:

- `json` — turns Python values into JSON text;
- `logging` — Python's built-in logging system. Code calls `logger.info(...)`, and the system routes the line to **handlers** (where it goes: the screen, a file) that use **formatters** (what it looks like);
- `datetime` and `UTC` — dates and times, in Coordinated Universal Time. Logs from servers in different countries can only be compared if they use one clock.

@@ 9
`FIELDS` — the extra details a log line may carry: which request (`request_id`), what kind (`method`, `path`), how it ended (`status`), and how long it took (`duration_ms`). Only these names are copied into the output, so a careless `extra={...}` elsewhere can't leak anything else.

@@ 12
`JsonFormatter` — our own formatter. It **inherits** from `logging.Formatter`: it is a Formatter in every way, except for the one method it replaces.

@@ 13
`format` is the method the logging system calls for every line. It receives a `LogRecord` — everything known about one log event — and must return the text to write.

@@ 14-19
The four fields every line has:

- `time` — when it happened. `record.created` is a plain number (seconds since 1 January 1970); `fromtimestamp(..., UTC)` turns it into a date and time in UTC, and `.isoformat(timespec="milliseconds")` writes it in the standard ISO 8601 form, to the thousandth of a second;
- `level` — how serious: `debug`, `info`, `warning`, `error` or `critical`, in lowercase;
- `logger` — which part of the program wrote it, such as `dwarpal.api`;
- `message` — the text itself. `getMessage()` fills in any placeholders, so `"unexpected %s"` becomes `"unexpected ValueError"`.

The annotation `dict[str, object]` tells the type checker that values of different types will be stored.

@@ 20
Copy in the extra details this record carries. `hasattr(record, name)` asks "does the record have this detail?", and `getattr` reads it. The braces build a **dict comprehension**: a dict built from a loop, in one expression.

@@ 21-22
If the line describes a crash, `record.exc_info` holds the error. `formatException` turns it into the usual **traceback** — the list of function calls that led to the error — which is what a developer needs to find the bug. A traceback shows lines of *code*, not the data that was being processed.

@@ 23
Turn the dict into one line of JSON. `ensure_ascii=False` keeps characters such as `—` or `é` readable, instead of escape codes like `—`.
