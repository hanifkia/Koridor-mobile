from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from typing import Optional

from app.core.entities import VehicleType


class CourierCreateSchema(BaseModel):
    """Schema for courier setup during terminal setup"""

    vehicle_type: VehicleType = Field(
        default=VehicleType.CAR,
        description="Type of vehicle the courier will use",
    )
    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Country where courier operates",
    )
    state: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="State/province where courier operates",
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="City where courier operates",
    )


class CourierUpdateSchema(BaseModel):
    vehicle_type: VehicleType | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None


class CourierResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    vehicle_type: VehicleType
    country: str
    state: str
    city: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
