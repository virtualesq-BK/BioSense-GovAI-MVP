# OpenAPI Contract

Canonical API specification for BioSense-GovAI.

- **Spec file:** `openapi.yaml` (OpenAPI 3.1)
- **Served at runtime:** `http://localhost:8000/docs` (FastAPI Swagger UI)

## Code Generation

```bash
# TypeScript client types (from apps/web)
npx openapi-typescript packages/openapi/openapi.yaml -o apps/web/src/types/api.ts
```

## Validation

```bash
pip install openapi-spec-validator
openapi-spec-validator packages/openapi/openapi.yaml
```
