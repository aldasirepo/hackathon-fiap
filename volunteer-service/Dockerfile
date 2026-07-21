# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd -m appuser
USER appuser

EXPOSE 8083
ENV PORT=8083

CMD ["python", "app.py"]
