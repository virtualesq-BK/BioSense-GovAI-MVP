FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/v1/health || exit 1

CMD ["sh", "-c", "uvicorn biosense.api.main:app --host 0.0.0.0 --port ${PORT}"]
