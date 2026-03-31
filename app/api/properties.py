"""
Property API endpoints.

GET  /api/properties         — List/search properties with filters.
GET  /api/properties/{id}    — Get detailed property view with images.
POST /api/properties         — (Owner only) Create a new listing.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_role
from app.crud import user as user_crud
from app.crud import property as property_crud
from app.schemas.property import PropertyCreate, PropertyOut, PropertyUpdate

router = APIRouter()


@router.get(
    "",
    response_model=list[PropertyOut],
    summary="List properties with optional filters",
)
def list_properties(
    locality: Optional[str] = Query(None, description="Search by locality name"),
    min_rent: Optional[int] = Query(None, ge=0, description="Minimum monthly rent"),
    max_rent: Optional[int] = Query(None, ge=0, description="Maximum monthly rent"),
    occupancy: Optional[str] = Query(
        None,
        pattern=r"^(single|double|triple)$",
        description="Occupancy type filter",
    ),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
):
    """
    Public endpoint — lists properties with optional search/filter.
    Returns paginated results with images included.
    """
    return property_crud.list_properties(
        db,
        locality=locality,
        min_rent=min_rent,
        max_rent=max_rent,
        occupancy_type=occupancy,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{property_id}",
    response_model=PropertyOut,
    summary="Get detailed property view",
)
def get_property(property_id: UUID, db: Session = Depends(get_db)):
    """Fetch a single property with its images and details."""
    prop = property_crud.get_property_by_id(db, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )
    return prop


@router.post(
    "",
    response_model=PropertyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property listing",
)
def create_property(
    data: PropertyCreate,
    current_user: CurrentUser = Depends(require_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    """
    Owner-only endpoint.
    Creates a property listing and attaches any provided image URLs.
    """
    # Look up the local user to get their UUID
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner profile not found. Sync your account first.",
        )

    return property_crud.create_property(db, owner_id=user.id, data=data)
