# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd -m appuser && chmod 1777 /tmp

USER appuser

EXPOSE 8081
ENV PORT=8081

CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--workers", "2", "--timeout", "60", "app:app"]
