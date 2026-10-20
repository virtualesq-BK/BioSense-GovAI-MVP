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


def test_verify_supabase_jwt_es256_via_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from jose import jwk

    from biosense.infrastructure.auth import supabase_jwt

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_jwk = {**jwk.construct(public_pem, "ES256").to_dict(), "kid": "test-kid"}
    monkeypatch.setattr(supabase_jwt, "_fetch_jwks", lambda: {"keys": [public_jwk]})
    monkeypatch.setattr(supabase_jwt, "_jwks_cache", None)

    token = jwt.encode(
        {
            "sub": "22222222-2222-2222-2222-222222222222",
            "email": "es@example.com",
            "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        },
        private_pem.decode(),
        algorithm="ES256",
        headers={"kid": "test-kid"},
    )
    user = verify_supabase_jwt(token)
    assert user.sub == "22222222-2222-2222-2222-222222222222"
    assert user.email == "es@example.com"
