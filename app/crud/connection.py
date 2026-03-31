"""
CRUD operations for the Connection (Handshake Engine) entity.

Duplicate-prevention logic lives here instead of a DB constraint,
so tenants can re-apply after a rejection or ended tenancy.
"""

from datetime import date
from uuid import UUID
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models.connection import Connection
from app.models.property import Property
from app.schemas.connection import ConnectionStatusUpdate


def get_connection_by_id(db: Session, connection_id: UUID) -> Optional[Connection]:
    return db.get(Connection, connection_id)


def check_duplicate_active_connection(
    db: Session, tenant_id: UUID, property_id: UUID,
) -> None:
    """
    Raise 400 if the tenant already has a pending or active_tenancy
    connection for this property. Allows re-applying after rejection/ended.
    """
    stmt = select(Connection).where(
        and_(
            Connection.tenant_id == tenant_id,
            Connection.property_id == property_id,
            Connection.status.in_(["pending", "accepted", "active_tenancy"]),
        )
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"You already have an active connection (status: {existing.status}) "
                f"for this property."
            ),
        )


def create_connection(
    db: Session, tenant_id: UUID, property_id: UUID,
) -> Connection:
    """
    Tenant initiates a connection request.
    Validates: no duplicate pending/active requests for the same property.
    """
    # Guard: duplicate check
    check_duplicate_active_connection(db, tenant_id, property_id)

    conn = Connection(
        tenant_id=tenant_id,
        property_id=property_id,
        status="pending",
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def update_connection_status(
    db: Session,
    connection: Connection,
    data: ConnectionStatusUpdate,
) -> Connection:
    """
    Owner updates connection status.
    Automatically sets tenancy_start_date when status becomes 'accepted'.
    """
    connection.status = data.status

    # Auto-set tenancy start date on acceptance
    if data.status == "accepted" and connection.tenancy_start_date is None:
        connection.tenancy_start_date = date.today()

    # Auto-set tenancy end date when ended
    if data.status == "ended" and connection.tenancy_end_date is None:
        connection.tenancy_end_date = date.today()

    db.commit()
    db.refresh(connection)
    return connection


def list_tenant_connections(db: Session, tenant_id: UUID) -> list[Connection]:
    """List all connections where this user is the tenant."""
    stmt = (
        select(Connection)
        .where(Connection.tenant_id == tenant_id)
        .order_by(Connection.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def list_owner_connections(db: Session, owner_id: UUID) -> list[Connection]:
    """
    List all connections for properties owned by this user.
    Joins through the Property table to find relevant connections.
    """
    stmt = (
        select(Connection)
        .join(Property, Connection.property_id == Property.id)
        .where(Property.owner_id == owner_id)
        .order_by(Connection.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
