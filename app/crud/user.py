"""
CRUD operations for the User entity.
"""

from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_clerk_id(db: Session, clerk_id: str) -> Optional[User]:
    stmt = select(User).where(User.clerk_id == clerk_id)
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, data: UserCreate) -> User:
    """Create a new user (called from Clerk webhook sync)."""
    user = User(
        clerk_id=data.clerk_id,
        role=data.role,
        full_name=data.full_name,
        email=data.email,
        phone_number=data.phone_number,
        profile_image_url=data.profile_image_url,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    """Partially update a user's profile fields."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
