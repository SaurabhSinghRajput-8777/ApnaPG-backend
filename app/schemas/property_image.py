"""
Pydantic schemas for the PropertyImage entity.
"""

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class PropertyImageCreate(BaseModel):
    property_id: UUID
    image_url: str
    is_cover_photo: bool = False


class PropertyImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID
    image_url: str
    is_cover_photo: bool
