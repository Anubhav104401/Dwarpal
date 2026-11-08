# The inference service's container image (Phase 8), built from the repository's root:
#   docker build -f services/inference/Dockerfile -t dwarpal-inference .
# Its models are not inside it: they are mounted read-only at /models (see infra/deploy/compose.yaml).

FROM python:3.13.17-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/inference/pyproject.toml services/inference/pyproject.toml
COPY libs/contracts/pyproject.toml libs/contracts/pyproject.toml
COPY libs/vision/pyproject.toml libs/vision/pyproject.toml
COPY ml/pyproject.toml ml/pyproject.toml
COPY packages/sdk-python/pyproject.toml packages/sdk-python/pyproject.toml
# The inference service, and the two libraries it uses.
COPY services/inference/src services/inference/src
COPY libs/contracts/src libs/contracts/src
COPY libs/vision/src libs/vision/src
RUN uv sync --locked --package dwarpal-inference --no-default-groups --no-editable

FROM python:3.13.17-slim-bookworm
# Tesseract, for reading documents' MRZ (§5.6.2): in production it is installed here, not in a separate container.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home dwarpal
COPY --from=build /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 DWARPAL_INFERENCE_MODELS_DIR=/models
USER dwarpal
WORKDIR /app
EXPOSE 8001
CMD ["uvicorn", "dwarpal_inference.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8001"]
