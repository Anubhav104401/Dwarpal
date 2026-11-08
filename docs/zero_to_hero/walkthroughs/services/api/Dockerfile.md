---
fingerprint: be2d7e7dbe016832
---
The **API's container image** (Phase 8, §5.8.2). Docker builds it from this recipe, in two *stages*: the first installs the dependencies; the second keeps only the result, which is smaller and carries no build tools an attacker could use.

@@ 1-3
What this file makes — the API's **container image**, a self-contained package of the program and everything it needs — how to build it (from the repository's root, so it can reach the shared libraries), and its two stages.

@@ 5
**Stage 1, `build`** — start from the official Python 3.13 image, its *slim* Debian 12 form, pinned to an exact release (3.13.17) that was at least a week old.

@@ 6-7
Copy the `uv` program out of uv's own official image, at the version the project uses everywhere (0.13.1).

@@ 8
uv's settings for an image: compile Python files to bytecode now (faster start), copy files rather than link them, and never download a Python — use the image's own.

@@ 9
Work in `/app`.

@@ 10-16
The workspace's description and lockfile, and each member's own `pyproject.toml`. uv needs every member's description to read the shared lockfile, even of members this image doesn't install.

@@ 18-20
Only the code the API needs: its own source, and the shared contracts. The inference service, the vision library and the ML code stay out.

@@ 21-22
Install exactly the lockfile's versions (`--locked`), for the API package and what it depends on only, without the developer tools (`--no-default-groups`), as real copies rather than links to the source (`--no-editable`) — so the source folders aren't needed at run time.

@@ 24
**Stage 2** — a fresh copy of the same Python image. Nothing from stage 1 comes along except what is copied on purpose: no uv, no build leftovers.

@@ 25-26
A **system user** with no password, no home and no login shell, number 10001. The API runs as it, so a flaw in the API can't act as `root` inside the container.

@@ 27-28
Copy in the installed environment from stage 1, and the logging settings (the same JSON log lines as in development).

@@ 29
Put the environment's programs first on the path, write output straight away (no buffering, so logs arrive at once), and mark this as **production** — where the API refuses development secrets and plain-HTTP addresses (§5.7.1).

@@ 30-32
Switch to that user, work in `/app`, and say that the service listens on port 8000.

@@ 33-35
Start the API with uvicorn on every address *inside* the container (only Caddy can reach it, on the private network). `--proxy-headers` with `--forwarded-allow-ips "*"` trusts the `X-Forwarded-For` header Caddy adds — which tells the API the visitor's real address, used by the per-address limits — safe here because nothing but Caddy can send requests to it.

@@ 17
And the Python SDK's (added 9 Nov). The SDK became a workspace member after this file was written; without its description uv couldn't read the workspace, and CI's first build of this image failed on it.
