"""
Pydantic schemas for the Connection (Handshake) entity.
"""

from datetime import date, datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request: Tenant initiates connection ────────────────────────
class ConnectionCreate(BaseModel):
    property_id: UUID


# ── Request: Owner updates status ───────────────────────────────
class ConnectionStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(accepted|rejected|active_tenancy|ended)$")


# ── Response ────────────────────────────────────────────────────
class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    property_id: UUID
    status: str
    tenancy_start_date: Optional[date] = None
    tenancy_end_date: Optional[date] = None
    created_at: datetime


# ── Enriched response (with tenant/property details) ────────────
class ConnectionDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    property_id: UUID
    status: str
    tenancy_start_date: Optional[date] = None
    tenancy_end_date: Optional[date] = None
    created_at: datetime

    # Nested details (populated via joins)
    tenant_name: Optional[str] = None
    tenant_email: Optional[str] = None
    tenant_phone: Optional[str] = None
    property_title: Optional[str] = None
    property_locality: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_id: Optional[UUID] = None
