"""
Review model — maps to the `reviews` table.
Enforces the Two-Way Trust Engine:
  - Reviews are gated: only unlocked when a connection status is
    'active_tenancy' or 'ended'.
  - Rating is constrained to 1–5.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Integer, Text, DateTime, ForeignKey,
    CheckConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    # ── Primary key ─────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Connection reference (the review is tied to a handshake) ─
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Author (who is writing the review) ──────────────────────
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Target (who is being reviewed) ──────────────────────────
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Review content ──────────────────────────────────────────
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Timestamps ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ───────────────────────────────────────────
    connection = relationship("Connection", back_populates="reviews")
    author = relationship("User", back_populates="authored_reviews", foreign_keys=[author_id])
    target_user = relationship("User", back_populates="received_reviews", foreign_keys=[target_user_id])

    # ── Constraints & Indexes ───────────────────────────────────
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        Index("ix_reviews_connection_id", "connection_id"),
        Index("ix_reviews_target_user_id", "target_user_id"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.rating}★ by={self.author_id} for={self.target_user_id}>"
