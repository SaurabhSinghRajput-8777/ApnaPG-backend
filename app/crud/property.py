"""
CRUD operations for the Property and PropertyImage entities.
"""

from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.property import Property
from app.models.property_image import PropertyImage
from app.schemas.property import PropertyCreate, PropertyUpdate


# ── Property CRUD ───────────────────────────────────────────────

def get_property_by_id(db: Session, property_id: UUID) -> Optional[Property]:
    """Fetch a property with its images eagerly loaded."""
    stmt = (
        select(Property)
        .options(selectinload(Property.images))
        .where(Property.id == property_id)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_properties(
    db: Session,
    *,
    locality: Optional[str] = None,
    min_rent: Optional[int] = None,
    max_rent: Optional[int] = None,
    occupancy_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Property]:
    """
    List properties with optional filters.
    Eagerly loads images for each property.
    """
    stmt = select(Property).options(selectinload(Property.images))

    if locality:
        stmt = stmt.where(Property.locality.ilike(f"%{locality}%"))
    if min_rent is not None:
        stmt = stmt.where(Property.monthly_rent >= min_rent)
    if max_rent is not None:
        stmt = stmt.where(Property.monthly_rent <= max_rent)
    if occupancy_type:
        stmt = stmt.where(Property.occupancy_type == occupancy_type)

    stmt = stmt.order_by(Property.created_at.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())


def create_property(
    db: Session,
    owner_id: UUID,
    data: PropertyCreate,
) -> Property:
    """Create a property listing and optional images."""
    prop = Property(
        owner_id=owner_id,
        title=data.title,
        description=data.description,
        locality=data.locality,
        latitude=data.latitude,
        longitude=data.longitude,
        monthly_rent=data.monthly_rent,
        occupancy_type=data.occupancy_type,
        house_rules=data.house_rules,
    )
    db.add(prop)
    db.flush()  # Get the ID before creating images

    # Attach images if provided
    if data.image_urls:
        for idx, url in enumerate(data.image_urls):
            img = PropertyImage(
                property_id=prop.id,
                image_url=url,
                is_cover_photo=(idx == 0),  # First image is cover
            )
            db.add(img)

    db.commit()
    db.refresh(prop)
    return prop


def update_property(db: Session, prop: Property, data: PropertyUpdate) -> Property:
    """Partially update a property listing."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return prop


# ── PropertyImage CRUD ──────────────────────────────────────────

def add_property_image(
    db: Session, property_id: UUID, image_url: str, is_cover: bool = False,
) -> PropertyImage:
    img = PropertyImage(
        property_id=property_id,
        image_url=image_url,
        is_cover_photo=is_cover,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return img


def delete_property(db: Session, property_id: UUID) -> None:
    """Delete a property listing (cascades handle images in DB)."""
    stmt = select(Property).where(Property.id == property_id)
    prop = db.execute(stmt).scalar_one_or_none()
    if prop:
        db.delete(prop)
        db.commit()
