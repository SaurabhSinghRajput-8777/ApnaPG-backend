"""
User model — maps to the `users` table.
Synced from Clerk via webhook; stores local profile data.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Enum as SAEnum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary key ─────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Clerk identity ──────────────────────────────────────────
    clerk_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )

    # ── Role (RBAC) ─────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        SAEnum("tenant", "owner", "admin", name="user_role_enum", create_constraint=True),
        nullable=False,
    )

    # ── Profile ─────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Timestamps ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    tenant_connections = relationship(
        "Connection", back_populates="tenant", foreign_keys="Connection.tenant_id",
    )
    authored_reviews = relationship(
        "Review", back_populates="author", foreign_keys="Review.author_id",
    )
    received_reviews = relationship(
        "Review", back_populates="target_user", foreign_keys="Review.target_user_id",
    )

    # ── Index ───────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User {self.full_name} ({self.role})>"
