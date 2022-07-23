FROM python:3.6.8-slim as base

WORKDIR /work

COPY requirements.txt .

RUN python3 -m pip install \
    --no-deps --no-cache-dir --disable-pip-version-check \
    -r requirements.txt

FROM base as docs

COPY requirements-docs.txt .

RUN python3 -m pip install \
    --no-deps --no-cache-dir --disable-pip-version-check \
    -r requirements-docs.txt