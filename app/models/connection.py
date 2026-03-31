"""
Connection model — maps to the `connections` table.
Implements the "Handshake Engine" state machine:
  pending → accepted → active_tenancy → ended
  pending → rejected
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum,
    ForeignKey, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Connection(Base):
    __tablename__ = "connections"

    # ── Primary key ─────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Tenant reference ────────────────────────────────────────
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Property reference ──────────────────────────────────────
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Handshake status (state machine) ────────────────────────
    status: Mapped[str] = mapped_column(
        SAEnum(
            "pending", "accepted", "rejected", "active_tenancy", "ended",
            name="connection_status_enum",
            create_constraint=True,
        ),
        default="pending",
        nullable=False,
    )

    # ── Tenancy dates ───────────────────────────────────────────
    tenancy_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tenancy_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Timestamps ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────
    tenant = relationship("User", back_populates="tenant_connections", foreign_keys=[tenant_id])
    property = relationship("Property", back_populates="connections")
    reviews = relationship("Review", back_populates="connection", cascade="all, delete-orphan")

    # ── Indexes (duplicate prevention handled at CRUD layer) ────
    __table_args__ = (
        Index("ix_connections_tenant_id", "tenant_id"),
        Index("ix_connections_property_id", "property_id"),
        Index("ix_connections_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Connection tenant={self.tenant_id} → property={self.property_id} [{self.status}]>"
