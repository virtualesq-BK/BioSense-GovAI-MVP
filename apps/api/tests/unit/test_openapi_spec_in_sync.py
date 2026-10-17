import importlib.util
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "export_openapi.py"


def test_committed_openapi_matches_fastapi_app() -> None:
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    committed = yaml.safe_load(module.OUTPUT.read_text(encoding="utf-8"))
    assert committed == yaml.safe_load(module.render()), (
        "packages/openapi/openapi.yaml is stale; run `python scripts/export_openapi.py`"
    )
