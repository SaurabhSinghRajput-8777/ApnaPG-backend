"""
Document API endpoints.

GET /api/documents/lease/{connection_id}  — Generate & download rental agreement PDF.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.crud import user as user_crud
from app.crud import property as property_crud
from app.crud import connection as connection_crud
from app.services.pdf_generator import generate_lease_pdf

router = APIRouter()


@router.get(
    "/lease/{connection_id}",
    summary="Generate & download rental agreement PDF",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Returns the rental agreement as a downloadable PDF.",
        },
    },
)
def get_lease_document(
    connection_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a Digital Rental Agreement PDF for a specific connection.

    Access control:
      - Only the tenant or the property owner can download.
      - Connection status must be 'accepted' or 'active_tenancy'.

    The PDF merges tenant details, owner details, property info,
    and house rules into a professional, downloadable document.
    """
    # ── 1. Look up the requesting user ──────────────────────────
    user = user_crud.get_user_by_clerk_id(db, current_user.clerk_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Sync your account first.",
        )

    # ── 2. Fetch the connection ─────────────────────────────────
    connection = connection_crud.get_connection_by_id(db, connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found.",
        )

    # ── 3. Fetch the property and determine the owner ───────────
    prop = property_crud.get_property_by_id(db, connection.property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated property not found.",
        )

    # ── 4. Authorization: must be tenant or owner ───────────────
    is_tenant = user.id == connection.tenant_id
    is_owner = user.id == prop.owner_id
    if not (is_tenant or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to access this document.",
        )

    # ── 5. Status check: only after acceptance ──────────────────
    if connection.status not in ("accepted", "active_tenancy"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Lease document is only available for accepted or active connections. "
                f"Current status: '{connection.status}'."
            ),
        )

    # ── 6. Fetch tenant and owner user records ──────────────────
    tenant = user_crud.get_user_by_id(db, connection.tenant_id)
    owner = user_crud.get_user_by_id(db, prop.owner_id)

    if not tenant or not owner:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load tenant or owner records.",
        )

    # ── 7. Build data dicts for the PDF generator ───────────────
    tenant_data = {
        "full_name": tenant.full_name,
        "email": tenant.email,
        "phone_number": tenant.phone_number,
    }

    owner_data = {
        "full_name": owner.full_name,
        "email": owner.email,
        "phone_number": owner.phone_number,
    }

    property_data = {
        "title": prop.title,
        "locality": prop.locality,
        "monthly_rent": prop.monthly_rent,
        "occupancy_type": prop.occupancy_type,
        "house_rules": prop.house_rules,
        "tenancy_start_date": connection.tenancy_start_date,
    }

    # ── 8. Generate the PDF ─────────────────────────────────────
    pdf_buffer = generate_lease_pdf(tenant_data, owner_data, property_data)

    # ── 9. Return as a downloadable PDF ─────────────────────────
    filename = f"ApnaPG_Lease_{connection_id}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
