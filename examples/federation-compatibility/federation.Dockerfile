FROM python:3.7.13-slim as base

WORKDIR /work

COPY requirements.txt .

RUN python3 -m pip install \
    --no-deps --no-cache-dir --disable-pip-version-check \
    -r requirements.txt

RUN python3 -m pip install flask==2.1.3 aiohttp==3.8.1

COPY examples/federation-compatibility/server.py .

EXPOSE 8080

CMD ["python3", "server.py"]
