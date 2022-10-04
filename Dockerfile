FROM python:3.7.13-slim as base

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
RUN python3 -m pip install importlib-metadata

FROM base as tests

COPY requirements-tests.txt .

RUN python3 -m pip install \
    --no-deps --no-cache-dir --disable-pip-version-check \
    -r requirements-tests.txt
RUN python3 -m pip install tox

RUN python3 -m pip install tox

FROM tests as examples

RUN python3 -m pip install \
    flask==2.1.3 \
    aiohttp==3.8.1
