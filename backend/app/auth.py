"""Who is calling? Supabase Auth issues the tokens; we ask Supabase to verify them."""

from dataclasses import dataclass

import httpx
from fastapi import Header, HTTPException

from app.config import get_settings

ROLE_TABLE = {"client": "requirements", "supplier": "offerings"}


@dataclass(frozen=True)
class User:
    id: str
    email: str
    role: str | None  # "client" | "supplier", chosen at sign-up
    company: str


def _verify(authorization: str) -> User:
    settings = get_settings()
    try:
        # Note: one Supabase round trip per authed request; verify the JWT locally
        # against the project's JWKS if this latency ever matters.
        response = httpx.get(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": authorization},
            timeout=10,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Login service unreachable, try again") from exc
    if response.status_code != 200:
        raise HTTPException(401, "Your session has expired. Please log in again.")
    data = response.json()
    meta = data.get("user_metadata") or {}
    return User(data["id"], data["email"].lower(), meta.get("role"), meta.get("company", ""))


def current_user(authorization: str | None = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in first.")
    return _verify(authorization)


def optional_user(authorization: str | None = Header(None)) -> User | None:
    return current_user(authorization) if authorization else None
