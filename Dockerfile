FROM python:3.10-slim AS base

WORKDIR /work

ENV PIP_VERSION=23.1.2
ENV UV_VERSION=0.10.11
ENV PYTHON_VERSION=3.10

RUN apt-get update && apt-get install -y libpq-dev && \
  # install base python deps
  pip install --upgrade pip==${PIP_VERSION} && pip install uv==${UV_VERSION}

COPY pyproject.toml .

RUN uv export --format requirements.txt --no-dev --no-emit-project --output-file requirements-base.txt && \
  uv pip install --system -r requirements-base.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS dev

RUN uv export --format requirements.txt --no-default-groups --group dev --no-emit-project --output-file requirements-dev.txt && \
  uv pip install --system -r requirements-dev.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS test

RUN uv export --format requirements.txt --no-default-groups --group dev --group test --no-emit-project --output-file requirements-test.txt && \
  uv pip install --system -r requirements-test.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS docs

RUN uv export --format requirements.txt --no-default-groups --group dev --group docs --no-emit-project --output-file requirements-docs.txt && \
  uv pip install --system -r requirements-docs.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS examples

RUN uv export --format requirements.txt --no-default-groups --group dev --group examples --no-emit-project --output-file requirements-examples.txt && \
  uv pip install --system -r requirements-examples.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match
