FROM python:3.10-slim AS base

WORKDIR /work

ENV PIP_VERSION=23.1.2
ENV PDM_VERSION=2.26.1
ENV UV_VERSION=0.5.31
ENV PYTHON_VERSION=3.10

RUN apt-get update && apt-get install -y libpq-dev && \
  # install base python deps
  pip install --upgrade pip==${PIP_VERSION} && pip install pdm==${PDM_VERSION} && pip install uv==${UV_VERSION}

# for pyproject.toml to extract version
COPY hiku/__init__.py ./hiku/__init__.py
# for pyproject.toml to read readme
COPY README.rst .

COPY pyproject.toml .
COPY pdm.lock .

RUN pdm export --prod -o requirements-base.txt -f requirements && \
  uv pip install --system -r requirements-base.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS dev

RUN pdm export -G dev -G lint -o requirements-dev.txt -f requirements && \
  uv pip install --system -r requirements-dev.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS test

RUN pdm export -G dev -G test -o requirements-test.txt -f requirements && \
  uv pip install --system -r requirements-test.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match && \
  uv pip install --system tox tox-pdm

FROM base AS docs

RUN pdm export -G dev -G docs -o requirements-docs.txt -f requirements && \
  uv pip install --system -r requirements-docs.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

FROM base AS examples

RUN pdm export -G dev -G examples -o requirements-examples.txt -f requirements && \
  uv pip install --system -r requirements-examples.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match
