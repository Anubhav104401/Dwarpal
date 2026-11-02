"""Turn on Dwarpal's alerts by email on the server (decided 2 Nov 2026): write Alertmanager's settings and the mail
password's file, and switch the `alerts` services on in `.env`.

Run on the server, in /opt/dwarpal, after gen_secrets.py:
    python3 alert_email.py --to you@example.org --smtp-host smtp.gmail.com:587 --smtp-user you@gmail.com
    docker compose up -d --wait

It asks for the mail account's password without showing it (for Gmail, an *app password*), so the password never
lands in the shell's history. Run it again to change any of them.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

# Plain addresses and `host:port` only: each value goes into a YAML file, so nothing that could end a line or a
# string gets in.
ADDRESS = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SMARTHOST = re.compile(r"[A-Za-z0-9.-]+:[0-9]{1,5}")

# Inside the Alertmanager container, where compose.yaml mounts the password's file.
PASSWORD_IN_CONTAINER = "/etc/alertmanager/smtp_password"  # noqa: S105 - a path, not a password


def alertmanager_config(to: str, smtp_host: str, smtp_user: str) -> str:
    """Alertmanager's settings: every alert goes by email to `to`, sent through the account `smtp_user`."""
    for value, pattern, name in (
        (to, ADDRESS, "--to"),
        (smtp_user, ADDRESS, "--smtp-user"),
        (smtp_host, SMARTHOST, "--smtp-host"),
    ):
        if not pattern.fullmatch(value):
            raise ValueError(f"{name}: {value!r} isn't a plain address")
    # JSON's quoted strings are valid YAML, quoted.
    quoted = {name: json.dumps(value) for name, value in (("to", to), ("host", smtp_host), ("user", smtp_user))}
    return f"""# Alertmanager's settings, written by alert_email.py: every alert goes by email to the owner.
global:
  smtp_smarthost: {quoted["host"]}
  smtp_from: {quoted["user"]}
  smtp_auth_username: {quoted["user"]}
  smtp_auth_password_file: {PASSWORD_IN_CONTAINER}
  smtp_require_tls: true
route:
  receiver: owner
  group_by: [alertname]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
receivers:
  - name: owner
    email_configs:
      - to: {quoted["to"]}
        send_resolved: true
"""


def switched_on(env: str, user: str) -> str:
    """The `.env` text with the alerts' three settings set (replaced if already there, added if not)."""
    settings = {
        "COMPOSE_PROFILES": "alerts",  # Compose starts the services marked `profiles: [alerts]`
        "DWARPAL_OTEL_ENDPOINT": "http://collector:4318",  # the API sends its metrics to the collector
        "DWARPAL_ALERT_USER": user,  # Alertmanager runs as the owner of the password's file, to read it
    }
    lines = [line for line in env.splitlines() if line.split("=", 1)[0] not in settings]
    lines += [f"{name}={value}" for name, value in settings.items()]
    return "\n".join(lines) + "\n"


def write_private(path: Path, text: str) -> None:
    """Write `text` to `path`, readable and writable by its owner only (0600), before a byte of it is written."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    path.chmod(0o600)  # an existing file keeps its old mode through os.open
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)


def current_user() -> str:
    """This account's `uid:gid`, as Compose's `user:` reads it (Windows, where tests run, has neither)."""
    if sys.platform == "win32":
        return "65534:65534"
    return f"{os.getuid()}:{os.getgid()}"


def main(argv: list[str] | None = None, ask: Callable[[str], str] = getpass.getpass) -> int:
    parser = argparse.ArgumentParser(description="Send Dwarpal's alerts by email.")
    parser.add_argument("--to", required=True, help="where the alerts go")
    parser.add_argument("--smtp-host", required=True, help="the mail server and port, such as smtp.gmail.com:587")
    parser.add_argument("--smtp-user", required=True, help="the account that sends them")
    parser.add_argument("--dir", type=Path, default=Path())
    args = parser.parse_args(argv)
    env_path = args.dir / ".env"
    if not env_path.exists():
        print(f"{env_path} doesn't exist: run gen_secrets.py first", file=sys.stderr)
        return 1
    try:
        config = alertmanager_config(args.to, args.smtp_host, args.smtp_user)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    password = ask("The mail account's password (not shown): ")
    if not password or password != ask("Once more: "):
        print("the passwords are empty or differ: nothing written", file=sys.stderr)
        return 1
    write_private(args.dir / "smtp_password", password)
    (args.dir / "alertmanager.yml").write_text(config, encoding="utf-8")
    # The .env keeps its owner-only mode: writing to an existing file doesn't change it.
    env_path.write_text(switched_on(env_path.read_text(encoding="utf-8"), current_user()), encoding="utf-8")
    print("alerts switched on: now run `docker compose up -d --wait`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
