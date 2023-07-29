FROM python:3.7.13-slim as base

WORKDIR /work

ENV PIP_VERSION=23.1.2
ENV PDM_VERSION=2.6
ENV PDM_USE_VENV=no
ENV PYTHONPATH=/work/__pypackages__/3.7/lib

RUN apt-get update && apt-get install -y libpq-dev && \
    pip install --upgrade pip==${PIP_VERSION} && pip install pdm==${PDM_VERSION}

# for pyproject.toml to extract version
COPY hiku/__init__.py ./hiku/__init__.py
# for pyproject.toml to read readme
COPY README.rst .

COPY pyproject.toml .
COPY pdm.lock .

RUN pdm sync --prod

FROM base as dev

RUN pdm sync -G dev

FROM base as docs

RUN pdm sync -G docs

FROM base as tests

RUN pdm sync -G test -G dev
RUN python3 -m pip install tox tox-pdm

FROM base as examples

RUN pdm sync -d -G dev -G examples
