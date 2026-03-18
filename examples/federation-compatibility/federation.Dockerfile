FROM python:3.10-slim

WORKDIR /work

ENV PIP_VERSION=23.1.2
ENV UV_VERSION=0.10.11
ENV PYTHON_VERSION=3.10

RUN apt-get update && apt-get install -y libpq-dev && \
  # install base python deps
  pip install --upgrade pip==${PIP_VERSION} && pip install uv==${UV_VERSION}

COPY pyproject.toml .

RUN uv export --format requirements.txt --no-default-groups --group dev --group examples --output-file requirements-examples.txt && \
  uv pip install --system -r requirements-examples.txt --no-deps --no-cache-dir --index-strategy unsafe-best-match

COPY examples/federation-compatibility/server.py .

EXPOSE 8080

CMD ["python3", "server.py"]
