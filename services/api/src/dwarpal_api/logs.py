"""Log lines as JSON — one object per line — so machines can search them and people can still read them."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

FIELDS = ("request_id", "method", "path", "status", "duration_ms")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        entry.update({name: getattr(record, name) for name in FIELDS if hasattr(record, name)})
        if record.exc_info:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)
