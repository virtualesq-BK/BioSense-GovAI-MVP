import time

import pytest
from jose import jwt

from biosense.config import settings
from biosense.infrastructure.auth.supabase_jwt import verify_supabase_jwt


def test_verify_supabase_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-jwt-secret"
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    token = jwt.encode(
        {
            "sub": "11111111-1111-1111-1111-111111111111",
            "email": "user@example.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        },
        secret,
        algorithm="HS256",
    )
    user = verify_supabase_jwt(token)
    assert user.sub == "11111111-1111-1111-1111-111111111111"
    assert user.email == "user@example.com"
