from dataclasses import dataclass

from jose import JWTError, jwt

from biosense.config import settings


@dataclass(frozen=True)
class SupabaseAuthUser:
    sub: str
    email: str | None


def verify_supabase_jwt(token: str) -> SupabaseAuthUser:
    if not settings.supabase_jwt_secret:
        raise ValueError("SUPABASE_JWT_SECRET is not configured")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise ValueError("Invalid Supabase JWT") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("JWT missing sub claim")

    email = payload.get("email")
    return SupabaseAuthUser(sub=str(sub), email=str(email) if email else None)
