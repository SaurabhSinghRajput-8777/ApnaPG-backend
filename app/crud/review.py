"""
CRUD operations for the Review (Two-Way Trust Engine) entity.

Enforces the review-gating rule: reviews can only be submitted
when a connection status is 'active_tenancy' or 'ended', and
the author must be part of that connection.
"""

from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.connection import Connection
from app.models.property import Property
from app.schemas.review import ReviewCreate


def validate_review_eligibility(
    db: Session,
    connection_id: UUID,
    author_id: UUID,
    target_user_id: UUID,
) -> Connection:
    """
    Enforce all review-gating rules:
      1. Connection must exist.
      2. Connection status must be 'active_tenancy' or 'ended'.
      3. Author must be part of the connection (tenant or property owner).
      4. Target must be the other party in the connection.
    Returns the Connection if valid, raises HTTPException otherwise.
    """
    connection = db.get(Connection, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found.",
        )

    if connection.status not in ("active_tenancy", "ended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Reviews can only be submitted for connections with status "
                f"'active_tenancy' or 'ended'. Current status: '{connection.status}'."
            ),
        )

    # Determine the owner_id of the property in this connection
    prop = db.get(Property, connection.property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated property not found.",
        )

    parties = {connection.tenant_id, prop.owner_id}

    if author_id not in parties:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not part of this connection.",
        )

    if target_user_id not in parties:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target user is not part of this connection.",
        )

    if author_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot review yourself.",
        )

    # Check if author already reviewed this connection
    existing = db.execute(
        select(Review).where(
            Review.connection_id == connection_id,
            Review.author_id == author_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a review for this connection.",
        )

    return connection


def create_review(db: Session, author_id: UUID, data: ReviewCreate) -> Review:
    """Create a review after validation passes."""
    validate_review_eligibility(
        db,
        connection_id=data.connection_id,
        author_id=author_id,
        target_user_id=data.target_user_id,
    )

    review = Review(
        connection_id=data.connection_id,
        author_id=author_id,
        target_user_id=data.target_user_id,
        rating=data.rating,
        review_text=data.review_text,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews_for_user(
    db: Session, user_id: UUID,
) -> tuple[list[Review], float | None, int]:
    """
    Fetch all reviews targeting a user, plus their aggregate rating.
    Returns: (reviews_list, average_rating, total_count)
    """
    # Aggregate
    agg_stmt = select(
        func.avg(Review.rating),
        func.count(Review.id),
    ).where(Review.target_user_id == user_id)
    row = db.execute(agg_stmt).one()
    avg_rating = round(float(row[0]), 2) if row[0] else None
    total = row[1]

    # Individual reviews
    reviews_stmt = (
        select(Review)
        .where(Review.target_user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    reviews = list(db.execute(reviews_stmt).scalars().all())

    return reviews, avg_rating, total
