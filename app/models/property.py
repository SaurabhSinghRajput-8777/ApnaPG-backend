"""
Property model — maps to the `properties` table.
Represents a PG/room listing created by an owner.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Text, Float, Integer, Boolean,
    Enum as SAEnum, DateTime, ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    # ── Primary key ─────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Owner reference ─────────────────────────────────────────
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Listing details ─────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    locality: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    monthly_rent: Mapped[int] = mapped_column(Integer, nullable=False)

    occupancy_type: Mapped[str] = mapped_column(
        SAEnum("single", "double", "triple", name="occupancy_type_enum", create_constraint=True),
        nullable=False,
    )

    is_verified_owner: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    # ── House rules (flexible JSONB) ────────────────────────────
    house_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ── Timestamps ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────
    owner = relationship("User", back_populates="properties")
    images = relationship(
        "PropertyImage", back_populates="property", cascade="all, delete-orphan",
    )
    connections = relationship(
        "Connection", back_populates="property", cascade="all, delete-orphan",
    )

    # ── Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_properties_locality", "locality"),
        Index("ix_properties_rent", "monthly_rent"),
    )

    def __repr__(self) -> str:
        return f"<Property '{self.title}' @ {self.locality}>"
