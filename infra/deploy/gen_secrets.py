"""Write the server's secrets file (`.env`) for infra/deploy/compose.yaml: every password and key made fresh and random.

Run once, on the server, in /opt/dwarpal — the secrets are made where they are used, and never travel:
    python3 gen_secrets.py --domain dwarpal-age.duckdns.org --email you@example.org --ghcr-owner your-github-name

The domain is a bare name: a free DuckDNS name (decision D40) or one you own. The file is readable by its owner only.
It refuses to overwrite an existing one: replacing the master key would make every stored signing key unreadable. The
demo shop's project ID and key are filled in later, by hand, once the console has made them (README, step 7).
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import secrets
import sys
from pathlib import Path

# One part of a name: letters and digits, with hyphens only inside, at most 63 characters.
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def domain_of(text: str) -> str:
    """The domain as Caddy and Compose use it — a bare name in lower case, such as `dwarpal-age.duckdns.org` — or
    `ValueError`. No `https://`, path, port or `*`: each would break the names made from it (`api.<domain>`)."""
    domain = text.strip().lower()
    labels = domain.split(".")
    # Two parts at least, each a proper label; the last isn't all digits, so an IP address is refused too.
    if len(labels) < 2 or not all(LABEL.fullmatch(label) for label in labels) or labels[-1].isdigit():
        raise ValueError(f"--domain must be a bare name such as dwarpal-age.duckdns.org, not {text!r}")
    if len(domain) > 253 - len("shop."):  # the longest name made from it must stay within DNS's 253 characters
        raise ValueError("--domain is too long: shop.<domain> would exceed 253 characters")
    return domain


def token(nbytes: int = 32) -> str:
    """A random secret of `nbytes` bytes, as URL-safe text (letters, digits, `-` and `_`: safe in a URL or .env)."""
    return secrets.token_urlsafe(nbytes)


def secrets_file(domain: str, email: str, owner: str) -> str:
    """The .env text: the settings given, and a fresh random value for every secret."""
    values = {
        "DWARPAL_DOMAIN": domain,
        "DWARPAL_ACME_EMAIL": email,
        "DWARPAL_GHCR_OWNER": owner.lower(),
        "DWARPAL_TAG": "latest",
        # 32 random bytes, base64, as the API's MasterKey reads it; it seals the token-signing keys (§5.4).
        "DWARPAL_MASTER_KEY": base64.b64encode(secrets.token_bytes(32)).decode(),
        "DWARPAL_DB_OWNER_PASSWORD": token(),
        "DWARPAL_DB_API_PASSWORD": token(),
        "DWARPAL_VALKEY_PASSWORD": token(),
        "DWARPAL_SHOP_SECRET": token(),
        "DWARPAL_SHOP_PROJECT_ID": "",
        "DWARPAL_SHOP_API_KEY": "",
    }
    lines = [f"{name}={value}" for name, value in values.items()]
    return (
        "# Dwarpal's secrets on this server (infra/deploy/gen_secrets.py). Never copy, commit or share.\n"
        + "\n".join(lines)
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a fresh .env of secrets for Dwarpal's server.")
    parser.add_argument("--domain", required=True, help="the domain, such as dwarpal-age.duckdns.org")
    parser.add_argument("--email", required=True, help="where Let's Encrypt writes about certificates")
    parser.add_argument("--ghcr-owner", required=True, help="the GitHub account whose GHCR holds the images")
    parser.add_argument("--out", type=Path, default=Path(".env"))
    args = parser.parse_args(argv)
    try:
        domain = domain_of(args.domain)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    if args.out.exists():
        print(f"{args.out} already exists: refusing to replace its secrets", file=sys.stderr)
        return 1
    # Created readable and writable by its owner only (0600), before a single secret is written into it.
    descriptor = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(secrets_file(domain, args.email, args.ghcr_owner))
    print(f"wrote {args.out} (readable by you only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
