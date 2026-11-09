"""Tests for the deployment's files (Phase 8): the secrets generator, and that the production Compose file asks for no
setting the generator doesn't write."""

from __future__ import annotations

import base64
import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
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


def test_the_domain_is_a_bare_name(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A free DuckDNS name or one's own (decision D40), in lower case; anything that would break the names made from
    it (`api.<domain>`) is refused before a single secret is written."""
    gen = generator()
    assert gen.domain_of(" Dwarpal-Age.DuckDNS.org ") == "dwarpal-age.duckdns.org"
    assert gen.domain_of("example.org") == "example.org"
    for bad in (
        "https://dwarpal-age.duckdns.org",  # a scheme
        "dwarpal-age.duckdns.org/",  # a path
        "dwarpal-age.duckdns.org:443",  # a port
        "*.duckdns.org",  # a wildcard
        "localhost",  # a single part
        "-dwarpal.duckdns.org",  # a hyphen at the start of a part
        "dwarpal..duckdns.org",  # an empty part
        "dwarpal.duckdns.org.",  # a trailing dot
        "203.0.113.7",  # an IP address
        "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 55 + ".org",  # 251 characters: shop.<it> is too long
        "",
    ):
        with pytest.raises(ValueError, match="--domain"):
            gen.domain_of(bad)
    out = tmp_path / ".env"
    args = ["--domain", "https://example.org", "--email", "a@example.org", "--ghcr-owner", "someone"]
    assert gen.main([*args, "--out", str(out)]) == 1
    assert "bare name" in capsys.readouterr().err
    assert not out.exists()


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


# A stand-in for `docker`: notes each command, reads any input it is given, answers the inference service's readiness
# question with `READYZ`, and — when asked — fails the first full start, as a deploy that doesn't come up healthy would.
FAKE_DOCKER = """#!/usr/bin/env bash
echo "$*" >> "$DOCKER_CALLS"
cat > /dev/null
if [[ "$*" == *"exec -T inference"* ]]; then printf '%s' "${READYZ:-}"; fi
if [ -n "${FAIL_FIRST_START:-}" ] && [[ "$*" == *--wait-timeout* ]] && [ ! -e "$DOCKER_CALLS.failed" ]; then
  touch "$DOCKER_CALLS.failed"
  exit 1
fi
"""
NEEDS_BASH = pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None, reason="runs deploy.sh in bash"
)


def deploy(
    folder: Path, key: str = "", unhealthy: bool = False, readyz: str = ""
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    """Run the real `deploy.sh` in `folder`, beside a `.env` from the real generator with the shop's key as given, and
    with the stand-in `docker` first on PATH. Its result, and every full start it asked for."""
    shutil.copy(DEPLOY / "deploy.sh", folder / "deploy.sh")
    settings = parse(generator().secrets_file("example.org", "a@example.org", "someone"))
    settings["DWARPAL_SHOP_API_KEY"] = key
    (folder / ".env").write_text("".join(f"{name}={value}\n" for name, value in settings.items()), encoding="utf-8")
    tools = folder / "bin"
    tools.mkdir()
    (tools / "docker").write_text(FAKE_DOCKER, encoding="utf-8")
    (tools / "docker").chmod(0o755)
    calls = folder / "calls.log"
    env = {**os.environ, "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}", "DOCKER_CALLS": str(calls)}
    env |= {"FAIL_FIRST_START": "1" if unhealthy else "", "READYZ": readyz}
    bash = shutil.which("bash")
    assert bash is not None
    run = subprocess.run(  # noqa: S603 - the repository's own script, with test settings
        [bash, str(folder / "deploy.sh"), "abc123"],
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    starts = [line for line in calls.read_text(encoding="utf-8").splitlines() if "--wait-timeout" in line]
    return run, starts


@NEEDS_BASH
@pytest.mark.parametrize("unhealthy", [False, True])
@pytest.mark.parametrize(("key", "left_out"), [("", True), ("dk_test_0123456789abcdefghij", False)])
def test_deploys_leave_out_the_shop_until_it_has_its_key(
    tmp_path: Path, key: str, left_out: bool, unhealthy: bool
) -> None:
    """The first deploy comes before the demo shop has a project and key (README, step 7): it can't serve a page
    then, so a deploy that waited for it would fail and roll back every time. `deploy.sh` leaves it out until
    the key is in .env — when deploying and when rolling back alike — and Caddy doesn't need it to start. The
    script really runs here, with `docker` replaced by a stand-in that notes what it is asked."""
    run, starts = deploy(tmp_path, key=key, unhealthy=unhealthy)
    assert run.returncode == (1 if unhealthy else 0), run.stderr
    assert len(starts) == (2 if unhealthy else 1)  # a failed start is followed by the rollback's
    assert all(("--scale shop=0" in line) == left_out for line in starts), starts
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    caddy = re.search(r"^  caddy:\n(?:(?:    .*)?\n)*?    depends_on: \[([^\]]*)\]", compose, re.MULTILINE)
    assert caddy is not None and "shop" not in caddy[1]


@NEEDS_BASH
@pytest.mark.parametrize(
    ("readyz", "warned"),
    [
        ('{"status":"ready","age_model":"stub-age-30","antispoof":"loaded","ocr":"ready"}', False),
        ('{"status":"ready","age_model":"stub-age-30","antispoof":"missing","ocr":"ready"}', True),
        ("", True),  # no answer at all
    ],
)
def test_a_deploy_says_when_the_anti_spoofing_networks_are_missing(tmp_path: Path, readyz: str, warned: bool) -> None:
    """The server starts without the anti-spoofing networks, but then refuses every live check — as CI found when it
    first started the inference image as the server does (9 Nov). So a deploy reports the inference service's readiness,
    and warns unless the networks are loaded; it still succeeds, since test checks work without them."""
    run, _ = deploy(tmp_path, readyz=readyz)
    assert run.returncode == 0, run.stderr
    assert ("anti-spoofing networks are missing" in run.stderr) == warned, run.stderr
    assert f"inference: {readyz or 'no answer'}" in run.stdout


def test_the_jobs_across_every_organisation_log_in_as_the_tables_owner() -> None:
    """Row-level security hides every organisation's rows from the services' login, `dwarpal_api`: the webhook worker,
    the hourly maintenance and the operator's tools would quietly find nothing to do — found on 9 Nov, before any
    deploy. They log in as the tables' owner; the API, which faces the internet, never does."""
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    owner = re.search(
        r"^x-owner-env: &owner-env\n  <<: \*api-env\n  DWARPAL_DATABASE_URL: (\S+)$", compose, re.MULTILINE
    )
    assert owner is not None, "compose.yaml: no x-owner-env settings"
    assert owner[1].startswith("postgresql+asyncpg://dwarpal:${DWARPAL_DB_OWNER_PASSWORD}@")
    expected = {"api": "api-env", "webhooks": "owner-env", "maintenance": "owner-env", "operator": "owner-env"}
    for service, settings in expected.items():
        block = re.search(rf"^  {service}:\n((?:(?:    .*)?\n)*)", compose, re.MULTILINE)
        assert block is not None, f"compose.yaml: no {service} service"
        assert f"    environment: *{settings}\n" in block[1], f"{service} should use *{settings}"
    assert "docker compose run --rm --no-deps operator migrate" in (DEPLOY / "deploy.sh").read_text(encoding="utf-8")


def test_both_python_images_copy_every_workspace_member_s_description() -> None:
    """uv reads the whole workspace to use the lockfile, so each Python image copies every member's pyproject.toml —
    one missing (the Python SDK, added after the images were written) fails the build. CI's first image builds found
    it (9 Nov); this keeps it found."""
    workspace = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = workspace["tool"]["uv"]["workspace"]["members"]
    found = [path.parent for pattern in patterns for path in REPO.glob(f"{pattern}/pyproject.toml")]
    members = sorted({member.relative_to(REPO).as_posix() for member in found})
    assert "packages/sdk-python" in members
    for image in ("services/api/Dockerfile", "services/inference/Dockerfile"):
        copied = re.findall(r"^COPY (\S+)/pyproject\.toml ", (REPO / image).read_text(encoding="utf-8"), re.MULTILINE)
        assert sorted(copied) == members, f"{image} copies {sorted(copied)}, the workspace has {members}"


def test_the_model_fetcher_gets_its_one_dependency_wherever_it_runs_without_the_project() -> None:
    """`fetch_models.py` imports httpx. Run without the project (`--no-project`), it must be given it — at the
    lockfile's version — or it fails before fetching anything, as CI's first image builds showed (9 Nov)."""
    locked = re.search(r'name = "httpx"\nversion = "([^"]+)"', (REPO / "uv.lock").read_text(encoding="utf-8"))
    assert locked is not None, "uv.lock: no httpx"
    for workflow in sorted((REPO / ".github" / "workflows").glob("*.yml")):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if "fetch_models.py" in line and "--no-project" in line:
                assert f"--with httpx=={locked[1]}" in line, f"{workflow.name}: {line.strip()}"


def test_the_uptime_check_runs_every_15_minutes_once_there_is_a_server() -> None:
    """Decision D33: the outside check runs every 15 minutes, never on the hour (when GitHub delays schedules most),
    with a token that may do nothing, and only once the API's public address is set; it asks the API's `/readyz`."""
    workflow = (REPO / ".github" / "workflows" / "uptime.yml").read_text(encoding="utf-8")
    cron = re.search(r'cron: "([\d,]+) \* \* \* \*"', workflow)
    assert cron is not None, "uptime.yml: no hourly cron line found"
    minutes = sorted(int(minute) for minute in cron[1].split(","))
    gaps = [b - a for a, b in zip(minutes, [*minutes[1:], minutes[0] + 60], strict=True)]
    assert gaps == [15, 15, 15, 15], f"uptime.yml runs at minutes {minutes}, not every 15 minutes"
    assert 0 not in minutes
    assert "permissions: {}" in workflow
    assert "if: vars.DWARPAL_PUBLIC_API_URL != ''" in workflow
    assert '"$API/readyz"' in workflow
