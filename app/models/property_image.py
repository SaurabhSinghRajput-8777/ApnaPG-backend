"""
PropertyImage model — maps to the `property_images` table.
Stores Cloudinary-hosted image URLs for a property listing.
"""

import uuid

from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PropertyImage(Base):
    __tablename__ = "property_images"

    # ── Primary key ─────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Property reference ──────────────────────────────────────
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Image data ──────────────────────────────────────────────
    image_url: Mapped[str] = mapped_column(String(512), nullable=False)
    is_cover_photo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Relationships ───────────────────────────────────────────
    property = relationship("Property", back_populates="images")

    # ── Indexes ─────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_property_images_property_id", "property_id"),
    )

    def __repr__(self) -> str:
        cover = " [COVER]" if self.is_cover_photo else ""
        return f"<PropertyImage {self.id}{cover}>"
