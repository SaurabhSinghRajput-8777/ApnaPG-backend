"""
Pydantic schemas for the User entity.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ── Request: Clerk webhook sync ─────────────────────────────────
class UserCreate(BaseModel):
    clerk_id: str
    role: str  # 'tenant' | 'owner' | 'admin'
    full_name: str
    email: str
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None


# ── Response ────────────────────────────────────────────────────
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clerk_id: str
    role: str
    full_name: str
    email: str
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime


# ── Compact version (for nested use in property/connection) ─────
class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    role: str
    profile_image_url: Optional[str] = None
