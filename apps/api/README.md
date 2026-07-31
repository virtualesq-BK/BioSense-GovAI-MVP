# BioSense-GovAI API

FastAPI backend with clean architecture.

## Run locally

```bash
pip install ".[dev]"
uvicorn biosense.api.main:app --reload --port 8000
```

## Test

```bash
pytest tests -v
```
