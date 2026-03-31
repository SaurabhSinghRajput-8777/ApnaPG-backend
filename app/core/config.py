"""
Application configuration loaded from environment variables.
Uses pydantic-style settings via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend root directory
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """Centralised settings — reads from environment variables."""

    # ── Database (Neon PostgreSQL) ──────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ── Clerk Authentication ────────────────────────────────────
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_JWKS_URL: str = os.getenv(
        "CLERK_JWKS_URL",
        "https://your-clerk-instance.clerk.accounts.dev/.well-known/jwks.json",
    )
    CLERK_ISSUER: str = os.getenv("CLERK_ISSUER", "")

    # ── Cloudinary ──────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # ── Application ─────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5173"
        ).split(",")
    ]


settings = Settings()
