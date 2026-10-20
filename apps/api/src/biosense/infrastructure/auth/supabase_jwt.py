import time
from dataclasses import dataclass
from typing import Any

import httpx
from jose import ExpiredSignatureError, JWTError, jwt

from biosense.config import settings

_ASYMMETRIC_ALGS = {"ES256", "RS256"}
_JWKS_TTL_SECONDS = 600.0

_jwks_cache: dict[str, Any] | None = None
_jwks_fetched_at = 0.0


@dataclass(frozen=True)
class SupabaseAuthUser:
    sub: str
    email: str | None


def _fetch_jwks() -> dict[str, Any]:
    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL is not configured")
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError("Unable to fetch Supabase JWKS") from exc
    return resp.json()


def _get_jwks(kid: str | None) -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at
    stale = _jwks_cache is None or time.monotonic() - _jwks_fetched_at > _JWKS_TTL_SECONDS
    # An unknown kid means Supabase rotated its signing keys.
    unknown_kid = kid is not None and _jwks_cache is not None and all(
        k.get("kid") != kid for k in _jwks_cache.get("keys", [])
    )
    if stale or unknown_kid:
        _jwks_cache = _fetch_jwks()
        _jwks_fetched_at = time.monotonic()
    return _jwks_cache


def _decode(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")
    if alg == "HS256":
        if not settings.supabase_jwt_secret:
            raise ValueError("SUPABASE_JWT_SECRET is not configured")
        key: Any = settings.supabase_jwt_secret
    elif alg in _ASYMMETRIC_ALGS:
        key = _get_jwks(header.get("kid"))
    else:
        raise JWTError(f"Unsupported JWT algorithm: {alg}")
    return jwt.decode(token, key, algorithms=[alg], audience="authenticated")


def verify_supabase_jwt(token: str) -> SupabaseAuthUser:
    try:
        payload = _decode(token)
    except ExpiredSignatureError as exc:
        raise ValueError("Supabase JWT has expired — please sign in again") from exc
    except JWTError as exc:
        raise ValueError("Invalid Supabase JWT") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("JWT missing sub claim")

    email = payload.get("email")
    return SupabaseAuthUser(sub=str(sub), email=str(email) if email else None)
