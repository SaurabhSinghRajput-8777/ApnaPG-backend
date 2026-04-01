"""
JWT / Clerk authentication middleware for FastAPI.

In production this will:
  1. Fetch Clerk's JWKS public keys.
  2. Decode & verify the Bearer JWT from the Authorization header.
  3. Extract `clerk_id` (sub) and `role` from token metadata.

For Phase 1.0 development, a lightweight mock mode is included so
endpoints can be tested without a live Clerk instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# ── Bearer token extractor ──────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=True)


# ── Authenticated user payload ──────────────────────────────────
@dataclass
class CurrentUser:
    """Data extracted from a verified Clerk JWT."""
    clerk_id: str
    role: str                     # 'tenant' | 'owner' | 'admin'
    email: Optional[str] = None
    full_name: Optional[str] = None


# ── JWT decoder ─────────────────────────────────────────────────
def _decode_clerk_token(token: str) -> dict:
    """
    Decode and verify a Clerk-issued JWT.

    In development mode (APP_ENV=development) without a configured
    CLERK_SECRET_KEY, this falls back to decoding WITHOUT verification
    so you can test with hand-crafted tokens.

    In production, the token is verified against Clerk's JWKS endpoint.
    """
    # ── Development / mock mode ────────────────────────────────
    if settings.APP_ENV == "development" and not settings.CLERK_SECRET_KEY:
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["RS256", "HS256"],
            )
            return payload
        except jwt.DecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {exc}",
            )

    # ── Production mode ────────────────────────────────────────
    try:
        # Fetch JWKS from Clerk and decode
        jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False},  # Clerk doesn't always set aud
            leeway=60,  # 60-second buffer for clock drift (fixes 'iat' and 'exp')
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error (Check CLERK_JWKS_URL bounds): {exc}",
        )


# ── FastAPI dependency ──────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    FastAPI dependency that extracts and validates the Clerk JWT.

    Usage in a route:
        @router.get("/protected")
        def protected(user: CurrentUser = Depends(get_current_user)):
            ...
    """
    payload = _decode_clerk_token(credentials.credentials)

    clerk_id: str = payload.get("sub", "")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim.",
        )

    # --- Role Extraction Logic ---
    role = payload.get("role")
    
    def _extract_from(obj):
        if isinstance(obj, dict):
            return obj.get("role")
        return None

    if not role: role = _extract_from(payload.get("public_metadata"))
    if not role: role = _extract_from(payload.get("metadata"))
    if not role: role = _extract_from(payload.get("unsafe_metadata"))

    # --- Clerk API Fallback (if JWT lacks metadata) ---
    if not role and settings.CLERK_SECRET_KEY:
        import httpx
        try:
            print(f"DEBUG: JWT missing role. Fetching from Clerk API for sub: {clerk_id}")
            with httpx.Client() as client:
                resp = client.get(
                    f"https://api.clerk.com/v1/users/{clerk_id}",
                    headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
                )
                if resp.status_code == 200:
                    user_data = resp.json()
                    # Check all metadata buckets in the API response
                    role = (
                        _extract_from(user_data.get("public_metadata")) or
                        _extract_from(user_data.get("private_metadata")) or
                        _extract_from(user_data.get("unsafe_metadata"))
                    )
                    print(f"DEBUG: Found role via Clerk API: {role}")
                else:
                    print(f"DEBUG: Clerk API failed with {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"DEBUG: Clerk API error: {e}")

    # Final fallback to tenant
    role = role or "tenant"

    return CurrentUser(
        clerk_id=clerk_id,
        role=role,
        email=payload.get("email"),
        full_name=payload.get("name"),
    )


# ── Role guard helpers ──────────────────────────────────────────
def require_role(*allowed_roles: str):
    """
    Returns a dependency that raises 403 if the user's role
    is not in the allowed set.

    Usage:
        @router.post("/properties", dependencies=[Depends(require_role("owner", "admin"))])
    """
    async def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorised for this action.",
            )
        return user
    return _guard
