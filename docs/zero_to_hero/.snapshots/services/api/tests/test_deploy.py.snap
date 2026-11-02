"""Tests for the deployment's files (Phase 8): the secrets generator, and that the production Compose file asks for no
setting the generator doesn't write."""

from __future__ import annotations

import base64
import importlib.util
import re
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[3]
DEPLOY = REPO / "infra" / "deploy"


def generator() -> ModuleType:
    """`infra/deploy/gen_secrets.py`, loaded as a module (it isn't part of any package)."""
    spec = importlib.util.spec_from_file_location("gen_secrets", DEPLOY / "gen_secrets.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#"))


def test_every_secret_is_fresh_and_the_master_key_is_32_random_bytes() -> None:
    gen = generator()
    one, two = (parse(gen.secrets_file("example.org", "a@example.org", "Someone")) for _ in range(2))
    assert len(base64.b64decode(one["DWARPAL_MASTER_KEY"], validate=True)) == 32
    for name in (
        "DWARPAL_MASTER_KEY",
        "DWARPAL_DB_OWNER_PASSWORD",
        "DWARPAL_DB_API_PASSWORD",
        "DWARPAL_VALKEY_PASSWORD",
    ):
        assert one[name] != two[name]  # made fresh each time
        assert len(one[name]) >= 32
    # The shop's signing secret must meet the shop's own minimum (lib/config.ts: 32 characters).
    assert len(one["DWARPAL_SHOP_SECRET"]) >= 32
    assert one["DWARPAL_GHCR_OWNER"] == "someone"  # GHCR's names are lower-case


def test_the_secrets_file_is_private_and_never_replaced(tmp_path: Path) -> None:
    gen = generator()
    out = tmp_path / ".env"
    args = ["--domain", "example.org", "--email", "a@example.org", "--ghcr-owner", "someone", "--out", str(out)]
    assert gen.main(args) == 0
    if sys.platform != "win32":  # Windows has no owner-only permission bits to check
        assert stat.S_IMODE(out.stat().st_mode) == 0o600
    before = out.read_text(encoding="utf-8")
    assert gen.main(args) == 1  # a second run refuses: replacing the master key would orphan the signing keys
    assert out.read_text(encoding="utf-8") == before


def test_compose_asks_only_for_settings_the_generator_writes() -> None:
    """Every `${NAME}` in the production Compose file is either written by the generator or has a default
    (`${NAME:-…}`), so a server set up by the README starts without a missing setting."""
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    written = set(parse(generator().secrets_file("example.org", "a@example.org", "someone")))
    wanted = set(re.findall(r"\$\{([A-Z_]+)\}", compose))
    assert wanted <= written, sorted(wanted - written)


@pytest.mark.parametrize("script", ["deploy.sh", "backup.sh", "restore_drill.sh"])
def test_scripts_stop_at_the_first_error(script: str) -> None:
    """`set -euo pipefail`: an unset value, a failed command or a failed part of a pipe stops the script — a backup
    or a deploy must never carry on half-done as if it had worked."""
    assert "set -euo pipefail" in (DEPLOY / script).read_text(encoding="utf-8")


def alert_email() -> ModuleType:
    """`infra/deploy/alert_email.py`, loaded as a module, as the secrets generator is."""
    spec = importlib.util.spec_from_file_location("alert_email", DEPLOY / "alert_email.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_alertmanager_settings_name_the_addresses_and_refuse_anything_else() -> None:
    mail = alert_email()
    config = mail.alertmanager_config("owner@example.org", "smtp.example.org:587", "sender@example.org")
    assert 'to: "owner@example.org"' in config
    assert 'smtp_smarthost: "smtp.example.org:587"' in config
    assert "smtp_auth_password_file: /etc/alertmanager/smtp_password" in config  # the password itself never
    # A value that could end the line, or the string, would let someone add their own settings.
    for bad in ("owner@example.org\n  smtp_from: x", 'owner"@example.org', "owner"):
        with pytest.raises(ValueError, match="--to"):
            mail.alertmanager_config(bad, "smtp.example.org:587", "sender@example.org")
    with pytest.raises(ValueError, match="--smtp-host"):
        mail.alertmanager_config("owner@example.org", "smtp.example.org", "sender@example.org")


def test_switching_alerts_on_twice_leaves_one_of_each_setting() -> None:
    mail = alert_email()
    env = "DWARPAL_DOMAIN=example.org\nCOMPOSE_PROFILES=old\n"
    once = mail.switched_on(env, "1000:1000")
    assert mail.switched_on(once, "1000:1000") == once
    values = parse(once)
    assert values["COMPOSE_PROFILES"] == "alerts"
    assert values["DWARPAL_OTEL_ENDPOINT"] == "http://collector:4318"
    assert values["DWARPAL_ALERT_USER"] == "1000:1000"
    assert values["DWARPAL_DOMAIN"] == "example.org"


def test_alert_email_writes_the_password_privately_and_only_when_typed_twice(tmp_path: Path) -> None:
    mail = alert_email()
    args = ["--to", "o@example.org", "--smtp-host", "smtp.example.org:587", "--smtp-user", "s@example.org"]
    args += ["--dir", str(tmp_path)]
    assert mail.main(args, ask=lambda _: "pw") == 1  # no .env yet: gen_secrets.py comes first
    (tmp_path / ".env").write_text("DWARPAL_DOMAIN=example.org\n", encoding="utf-8")
    answers = iter(["one", "two"])
    assert mail.main(args, ask=lambda _: next(answers)) == 1  # typed differently: nothing written
    assert not (tmp_path / "smtp_password").exists()
    assert mail.main(args, ask=lambda _: "the password") == 0
    assert (tmp_path / "smtp_password").read_text(encoding="utf-8") == "the password"
    assert "the password" not in (tmp_path / "alertmanager.yml").read_text(encoding="utf-8")
    assert parse((tmp_path / ".env").read_text(encoding="utf-8"))["COMPOSE_PROFILES"] == "alerts"
    if sys.platform != "win32":
        assert stat.S_IMODE((tmp_path / "smtp_password").stat().st_mode) == 0o600


def test_the_deploy_copies_every_file_compose_mounts() -> None:
    """Each `./file` the production Compose file mounts is copied to the server by the deploy workflow, or written on
    the server itself (the models, and the alerts' mail settings)."""
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    workflow = (REPO / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    mounted = set(re.findall(r"- \./([\w.]+):", compose))
    made_on_the_server = {"models", "alertmanager.yml", "smtp_password"}
    copied = {name.rsplit("/", 1)[-1] for name in re.findall(r"[\w./]+\.(?:yaml|sh|py)|Caddyfile", workflow)}
    assert mounted - made_on_the_server <= copied, sorted(mounted - made_on_the_server - copied)
