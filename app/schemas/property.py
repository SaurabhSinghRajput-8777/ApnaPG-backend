"""
Pydantic schemas for the Property entity.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request: Create property ────────────────────────────────────
class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = ""
    locality: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    monthly_rent: int = Field(..., gt=0)
    occupancy_type: str = Field(..., pattern=r"^(single|double|triple)$")
    house_rules: Optional[dict] = None
    image_urls: Optional[list[str]] = None  # Cloudinary URLs sent from frontend


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    locality: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    monthly_rent: Optional[int] = Field(None, gt=0)
    occupancy_type: Optional[str] = Field(None, pattern=r"^(single|double|triple)$")
    house_rules: Optional[dict] = None


# ── Response: Property image (nested) ───────────────────────────
class PropertyImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_url: str
    is_cover_photo: bool


# ── Response: Property listing ──────────────────────────────────
class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    title: str
    description: str
    locality: str
    latitude: float
    longitude: float
    monthly_rent: int
    occupancy_type: str
    is_verified_owner: bool
    house_rules: Optional[dict] = None
    created_at: datetime
    images: list[PropertyImageOut] = []


# ── Compact version for connection/search results ──────────────
class PropertyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    locality: str
    monthly_rent: int
    occupancy_type: str
    is_verified_owner: bool
