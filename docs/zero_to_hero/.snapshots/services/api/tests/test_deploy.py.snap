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
