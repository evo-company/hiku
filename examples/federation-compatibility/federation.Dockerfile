FROM python:3.8.18-slim as base

WORKDIR /work

ENV PIP_VERSION=23.1.2
ENV PDM_VERSION=2.7.4
ENV PDM_USE_VENV=no
ENV PYTHONPATH=/work/__pypackages__/3.8/lib

RUN apt-get update && apt-get install -y libpq-dev gcc && \
    pip install --upgrade pip==${PIP_VERSION} && pip install pdm==${PDM_VERSION}

# for pyproject.toml to extract version
COPY hiku/__init__.py ./hiku/__init__.py
# for pyproject.toml to read readme
COPY README.rst .

COPY pyproject.toml .
COPY pdm.lock .

RUN pdm sync -G dev -G examples

COPY examples/federation-compatibility/server.py .

EXPOSE 8080

CMD ["python3", "server.py"]
