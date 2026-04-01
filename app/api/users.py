"""
User API endpoints.

POST /api/users/sync  — Clerk webhook to create/sync a user in our DB.
GET  /api/users/me     — Get current authenticated user's profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserOut

router = APIRouter()


@router.post(
    "/sync",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Sync user from Clerk",
)
def sync_user(data: UserCreate, db: Session = Depends(get_db)):
    """
    Webhook endpoint for Clerk.
    Creates a user in the local DB if they don't exist,
    or returns the existing record.
    """
    from sqlalchemy.exc import IntegrityError

    existing = user_crud.get_user_by_clerk_id(db, data.clerk_id)
    if existing:
        return existing
        
    # Check if the user recreated their Clerk account using the same email
    existing_email = user_crud.get_user_by_email(db, data.email)
    if existing_email:
        existing_email.clerk_id = data.clerk_id
        db.commit()
        db.refresh(existing_email)
        return existing_email
        
    try:
        return user_crud.create_user(db, data)
    except IntegrityError:
        db.rollback()
        return user_crud.get_user_by_clerk_id(db, data.clerk_id)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
)
def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the authenticated user's full profile from our DB."""
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync your account first.",
        )
    return user


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Update current user profile",
)
def update_my_profile(
    data: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile fields."""
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user_crud.update_user(db, user, data)
