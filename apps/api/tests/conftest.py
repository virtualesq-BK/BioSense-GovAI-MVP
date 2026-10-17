import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(autouse=True)
def _authenticated_admin(request, monkeypatch):
    """Default: requests act as an admin. test_auth_guards.py opts out to test real guards."""
    if request.module.__name__.endswith("test_auth_guards"):
        yield
        return
    from biosense.api.dependencies import get_current_user
    from biosense.api.main import app
    from biosense.config import settings
    from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser

    monkeypatch.setattr(settings, "admin_emails", "admin@test.local")
    admin = SupabaseAuthUser("admin", "admin@test.local")
    app.dependency_overrides[get_current_user] = lambda: admin
    yield
    app.dependency_overrides.pop(get_current_user, None)
