from uuid import UUID

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime, time, timedelta
from decimal import Decimal

from app.core.entities import VehicleType, FuelType


class TerminalCreateSchema(BaseModel):
    """Schema for terminal/hub setup during courier onboarding"""

    # Hub/Terminal information
    terminal_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Name of the terminal/hub",
    )
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude coordinate of hub location",
    )
    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude coordinate of hub location",
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Physical address of the hub",
    )

    # Time settings (in minutes)
    setup_time: Optional[int] = Field(
        default=15,
        ge=1,
        le=480,
        description="Hub setup time in minutes (1-480)",
    )
    service_time: Optional[int] = Field(
        default=30,
        ge=1,
        le=480,
        description="Service time per stop in minutes (1-480)",
    )

    # Hub configuration
    return_to_hub: Optional[bool] = Field(
        default=True,
        description="Whether courier must return to hub after deliveries",
    )

    # Validators for additional validation
    @validator("terminal_name")
    def validate_terminal_name(cls, v):
        """Validate terminal name"""
        if not v or not v.strip():
            raise ValueError("Terminal name cannot be empty")
        return v.strip()

    @validator("latitude", "longitude")
    def validate_coordinates(cls, v):
        """Validate coordinates are valid numbers"""
        if v is None:
            raise ValueError("Coordinates cannot be None")
        return float(v)

    class Config:
        """Pydantic config"""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "terminal_name": "Manhattan Hub",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Main Street, New York, NY 10001",
                "setup_time": 15,
                "service_time": 30,
                "return_to_hub": True,
            }
        }


class TerminalUpdateSchema(BaseModel):
    terminal_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    setup_time: int | None = None
    service_time: int | None = None
    return_to_hub: bool | None = None


class ShiftCreateSchema(BaseModel):
    """Schema for creating a hub shift"""

    start_time: time = Field(
        ...,
        description="Shift start time (HH:MM:SS format)",
    )
    finish_time: time = Field(
        ...,
        description="Shift finish time (HH:MM:SS format)",
    )

    @validator("finish_time")
    def validate_times(cls, v, values):
        """Validate finish time is after start time"""
        if "start_time" in values:
            start_time = values["start_time"]
            if v <= start_time:
                raise ValueError("Finish time must be after start time")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "start_time": "08:00:00",
                "finish_time": "17:00:00",
            }
        }


class ShiftResponseSchema(BaseModel):
    """Schema for shift response"""

    id: str
    terminal_id: str
    start_time: time
    finish_time: time
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ShiftConflictSchema(BaseModel):
    """Schema for shift conflict details"""

    existing_shift_id: str
    existing_start_time: time
    existing_finish_time: time
    new_start_time: time
    new_finish_time: time
    overlap_type: (
        str  # "full", "partial_start", "partial_end", "contains", "contained_in"
    )


class TerminalResponseSchema(BaseModel):
    id: UUID
    courier_id: UUID
    name: str
    lat: float
    lon: float
    address: Optional[str] = None
    setup_time: timedelta
    service_time: timedelta | None = (
        None  # TODO: Make service_time required after we have it in the database
    )
    return_to_hub: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
