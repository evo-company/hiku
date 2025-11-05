FROM python:3.10-slim

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

RUN pdm export -G dev -G examples -o requirements-examples.txt -f requirements && \
  uv pip install --system -r requirements-examples.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

COPY examples/federation-compatibility/server.py .

EXPOSE 8080

CMD ["python3", "server.py"]
