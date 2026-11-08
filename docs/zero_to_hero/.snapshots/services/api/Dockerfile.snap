# The API's container image (Phase 8). Built from the repository's root, for Arm and Intel alike:
#   docker build -f services/api/Dockerfile -t dwarpal-api .
# Two stages: the first installs the locked dependencies with uv; the second keeps only the result, with no build tools.

FROM python:3.13.17-slim-bookworm AS build
# uv, the same version as the project uses everywhere else, copied from its official image.
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# The workspace's description and lockfile, and every member's own description: uv needs them all to read the lock.
COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/inference/pyproject.toml services/inference/pyproject.toml
COPY libs/contracts/pyproject.toml libs/contracts/pyproject.toml
COPY libs/vision/pyproject.toml libs/vision/pyproject.toml
COPY ml/pyproject.toml ml/pyproject.toml
COPY packages/sdk-python/pyproject.toml packages/sdk-python/pyproject.toml
# Only the code the API needs: its own, and the shared contracts.
COPY services/api/src services/api/src
COPY libs/contracts/src libs/contracts/src
# Exactly the lockfile's versions (--locked), only the API and what it uses, no developer tools, installed as copies.
RUN uv sync --locked --package dwarpal-api --no-default-groups --no-editable

FROM python:3.13.17-slim-bookworm
# A user with no rights and no login, so a flaw in the service can't act as root.
RUN useradd --system --uid 10001 --no-create-home dwarpal
COPY --from=build /app/.venv /app/.venv
COPY services/api/logging.json /app/logging.json
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 DWARPAL_ENVIRONMENT=production
USER dwarpal
WORKDIR /app
EXPOSE 8000
# Answers only to Caddy, on the private network; trusts its forwarded addresses (--proxy-headers) from there alone.
CMD ["uvicorn", "dwarpal_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*", "--log-config", "/app/logging.json"]
