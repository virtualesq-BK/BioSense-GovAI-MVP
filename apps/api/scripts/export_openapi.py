"""Regenerate packages/openapi/openapi.yaml from the FastAPI app.

Run from apps/api:  python scripts/export_openapi.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml  # noqa: E402

from biosense.api.main import app  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[3] / "packages" / "openapi" / "openapi.yaml"


def render() -> str:
    return yaml.safe_dump(app.openapi(), sort_keys=True, allow_unicode=True)


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
