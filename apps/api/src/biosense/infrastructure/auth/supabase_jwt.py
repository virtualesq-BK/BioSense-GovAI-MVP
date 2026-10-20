from dataclasses import dataclass

from jose import ExpiredSignatureError, JWTError, jwt

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
    except ExpiredSignatureError as exc:
        raise ValueError("Supabase JWT has expired — please sign in again") from exc
    except JWTError as exc:
        # Decode without verification to inspect the token for debugging
        try:
            unverified = jwt.get_unverified_claims(token)
            aud = unverified.get("aud")
            if aud and aud != "authenticated":
                raise ValueError(f"Invalid JWT audience: expected 'authenticated', got '{aud}'") from exc
        except Exception:
            pass
        raise ValueError("Invalid Supabase JWT") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("JWT missing sub claim")

    email = payload.get("email")
    return SupabaseAuthUser(sub=str(sub), email=str(email) if email else None)
