"""
Pydantic schemas for the Review (Two-Way Trust Engine) entity.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request: Submit review ──────────────────────────────────────
class ReviewCreate(BaseModel):
    connection_id: UUID
    target_user_id: UUID
    rating: int = Field(..., ge=1, le=5)
    review_text: str = ""


# ── Response ────────────────────────────────────────────────────
class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connection_id: UUID
    author_id: UUID
    target_user_id: UUID
    rating: int
    review_text: str
    created_at: datetime


# ── Aggregate for a user's profile ──────────────────────────────
class UserReviewSummary(BaseModel):
    user_id: UUID
    average_rating: Optional[float] = None
    total_reviews: int = 0
    reviews: list[ReviewOut] = []
