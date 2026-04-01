"""
Connection (Handshake Engine) API endpoints.

POST  /api/connections              — Tenant requests a connection.
GET   /api/connections/me           — List my connections (context-aware).
PATCH /api/connections/{id}/status  — Owner accepts/rejects a connection.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_role
from app.crud import user as user_crud
from app.crud import connection as connection_crud
from app.crud import property as property_crud
from app.models.property import Property
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionDetailOut,
    ConnectionStatusUpdate,
)

router = APIRouter()


def _enrich_connection(db: Session, conn) -> dict:
    """
    Build a ConnectionDetailOut dict by joining tenant/property/owner data.
    This provides the enriched dashboard view.
    """
    tenant = user_crud.get_user_by_id(db, conn.tenant_id)
    prop = property_crud.get_property_by_id(db, conn.property_id)
    owner = user_crud.get_user_by_id(db, prop.owner_id) if prop else None

    # Phone numbers are only revealed if connection is accepted or beyond
    reveal_contact = conn.status in ("accepted", "active_tenancy", "ended")

    return {
        "id": conn.id,
        "tenant_id": conn.tenant_id,
        "property_id": conn.property_id,
        "status": conn.status,
        "tenancy_start_date": conn.tenancy_start_date,
        "tenancy_end_date": conn.tenancy_end_date,
        "created_at": conn.created_at,
        "tenant_name": tenant.full_name if tenant else None,
        "tenant_email": tenant.email if tenant else None,
        "tenant_phone": tenant.phone_number if (tenant and reveal_contact) else None,
        "property_title": prop.title if prop else None,
        "property_locality": prop.locality if prop else None,
        "owner_name": owner.full_name if owner else None,
        "owner_phone": owner.phone_number if (owner and reveal_contact) else None,
        "owner_id": owner.id if owner else None,
    }


@router.post(
    "",
    response_model=ConnectionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Request a connection (tenant only)",
)
def create_connection(
    data: ConnectionCreate,
    current_user: CurrentUser = Depends(require_role("tenant")),
    db: Session = Depends(get_db),
):
    """
    Tenant initiates a handshake request for a property.
    Validates the property exists and no duplicate active request.
    """
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Sync your account first.",
        )

    # Validate property exists
    prop = property_crud.get_property_by_id(db, data.property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    return connection_crud.create_connection(db, tenant_id=user.id, property_id=data.property_id)


@router.get(
    "/me",
    response_model=list[ConnectionDetailOut],
    summary="List my connections (context-aware)",
)
def list_my_connections(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Context-aware connection listing:
      - Tenants see requests they've made.
      - Owners see requests received for their properties.
    Phone numbers are masked until a connection is accepted.
    """
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.role == "tenant":
        connections = connection_crud.list_tenant_connections(db, user.id)
    else:
        connections = connection_crud.list_owner_connections(db, user.id)

    return [_enrich_connection(db, c) for c in connections]


@router.patch(
    "/{connection_id}/status",
    response_model=ConnectionOut,
    summary="Update connection status (owner only)",
)
def update_connection_status(
    connection_id: UUID,
    data: ConnectionStatusUpdate,
    current_user: CurrentUser = Depends(require_role("owner", "admin")),
    db: Session = Depends(get_db),
):
    """
    Owner accepts or rejects a connection request.
    On acceptance, tenancy_start_date is auto-set to today.
    On ending, tenancy_end_date is auto-set to today.
    """
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    conn = connection_crud.get_connection_by_id(db, connection_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found.",
        )

    # Verify that this owner actually owns the property
    prop = property_crud.get_property_by_id(db, conn.property_id)
    if not prop or prop.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own the property associated with this connection.",
        )

    return connection_crud.update_connection_status(db, conn, data)
