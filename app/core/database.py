"""
Database engine, session factory, and dependency for FastAPI.
Connects to Neon Serverless PostgreSQL via SQLAlchemy 2.0.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# ── Engine ──────────────────────────────────────────────────────
# Neon requires SSL; the connection string already contains ?sslmode=require.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Reconnect on stale connections
    pool_size=5,              # Keep pool small for serverless
    max_overflow=10,
    echo=settings.APP_DEBUG,  # Log SQL in dev only
)

# ── Session Factory ─────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Declarative Base ────────────────────────────────────────────
class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base for all models."""
    pass


# ── FastAPI Dependency ──────────────────────────────────────────
def get_db():
    """
    Yields a database session per request, ensuring it is closed
    after the request completes (even on error).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
