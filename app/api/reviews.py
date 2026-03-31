"""
Review (Two-Way Trust Engine) API endpoints.

POST /api/reviews              — Submit a gated review.
GET  /api/reviews/user/{id}    — Fetch reviews & aggregate rating for a user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.crud import user as user_crud
from app.crud import review as review_crud
from app.schemas.review import ReviewCreate, ReviewOut, UserReviewSummary

router = APIRouter()


@router.post(
    "",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review (gated)",
)
def create_review(
    data: ReviewCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a review for the other party in a connection.

    Enforced rules (validated in CRUD layer):
      1. Connection must exist.
      2. Connection status must be 'active_tenancy' or 'ended'.
      3. Author must be part of the connection (tenant or property owner).
      4. Target must be the other party.
      5. No self-reviews.
      6. No duplicate reviews per connection per author.
    """
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Sync your account first.",
        )

    return review_crud.create_review(db, author_id=user.id, data=data)


@router.get(
    "/user/{user_id}",
    response_model=UserReviewSummary,
    summary="Get reviews for a user",
)
def get_user_reviews(user_id: UUID, db: Session = Depends(get_db)):
    """
    Fetch aggregate rating and individual reviews for a specific user.
    This is a public endpoint used to display trust ratings on profiles.
    """
    target = user_crud.get_user_by_id(db, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    reviews, avg_rating, total = review_crud.get_reviews_for_user(db, user_id)

    return UserReviewSummary(
        user_id=user_id,
        average_rating=avg_rating,
        total_reviews=total,
        reviews=reviews,
    )
