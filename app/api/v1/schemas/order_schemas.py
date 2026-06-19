"""
Order request/response schemas
"""

from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime, time, date
from typing import Optional

from app.core.entities import OrderStatusTypes


class CoordinatesSchema(BaseModel):
    """Coordinates schema"""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")

    class Config:
        json_schema_extra = {"example": {"lat": 40.7128, "lon": -74.0060}}
        from_attributes = True


class AddressSchema(BaseModel):
    """Address schema"""

    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal code")

    class Config:
        json_schema_extra = {
            "example": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postal_code": "10001",
            }
        }
        from_attributes = True


class TimeWindowSchema(BaseModel):
    """Time window schema"""

    earliest: time = Field(..., description="Earliest delivery time")
    latest: time = Field(..., description="Latest delivery time")

    @validator("latest")
    def validate_time_window(cls, v, values):
        if "earliest" in values and v <= values["earliest"]:
            raise ValueError("Latest time must be after earliest time")
        return v

    class Config:
        from_attributes = True


class CreateRecipientRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Recipient name")
    phone_number: str = Field(
        ..., min_length=10, max_length=20, description="Recipient phone number"
    )
    email: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Recipient email"
    )
    location: Optional[CoordinatesSchema] = Field(
        None, description="Location coordinates"
    )
    address: Optional[AddressSchema] = Field(None, description="Delivery address")


class CreateOrderRequest(BaseModel):
    """Create order request"""

    name: str = Field(..., min_length=1, max_length=255, description="Order name")
    barcode: str = Field(..., min_length=1, max_length=100, description="Order barcode")
    time_window: Optional[TimeWindowSchema] = Field(None, description="Time window")
    weight_occupation: float = Field(0.0, ge=0, description="Weight in kg")
    volume_occupation: float = Field(0.0, ge=0, description="Volume in cubic meters")
    recipient: CreateRecipientRequest = Field(..., description="Recipient details")
    expected_delivery_date: Optional[date] = Field(
        None, description="Expected delivery date"
    )
    geo_location_provided: bool = Field(False, description="Is geo location provided")
    is_return: bool = Field(False, description="Is return order")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Package A",
                "barcode": "PKG123456",
                "time_window": {
                    "earliest": "09:00:00",
                    "latest": "17:00:00",
                },
                "weight_occupation": 2.5,
                "volume_occupation": 0.5,
                "recipient": {
                    "name": "John Doe",
                    "phone_number": "+1234567890",
                    "email": "jRyH2@example.com",
                    "location": {"lat": 40.7128, "lon": -74.0060},
                    "address": {
                        "street": "123 Main St",
                        "city": "New York",
                        "state": "NY",
                        "country": "USA",
                        "postal_code": "10001",
                    },
                },
                "expected_delivery_date": "2024-01-15",
                "is_return": False,
            }
        }


class UpdateOrderRequest(BaseModel):
    """Update order request"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    barcode: Optional[str] = Field(None, min_length=1, max_length=100)
    location: Optional[CoordinatesSchema] = None
    address: Optional[AddressSchema] = None
    time_window: Optional[TimeWindowSchema] = None
    weight_occupation: Optional[float] = Field(None, ge=0)
    volume_occupation: Optional[float] = Field(None, ge=0)
    expected_delivery_date: Optional[datetime] = None
    is_return: Optional[bool] = Field(None, description="Is return order")
    recipient: Optional[CreateRecipientRequest] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Package A",
                "barcode": "PKG123456",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "postal_code": "10001",
                },
                "time_window": {
                    "earliest": "09:00:00",
                    "latest": "17:00:00",
                },
                "weight_occupation": 2.5,
                "volume_occupation": 0.5,
                "expected_delivery_date": "2024-01-15",
            }
        }


class RecipientSchema(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    location: Optional[CoordinatesSchema] = None
    address: Optional[AddressSchema] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema"""

    # Identifiers
    id: UUID
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    recipient_id: UUID

    # Order details
    name: str
    barcode: str
    status: OrderStatusTypes

    # Time window (from shift)
    time_window: Optional[TimeWindowSchema] = None

    # Capacity
    weight_occupation: float = Field(default=0.0, ge=0)
    volume_occupation: float = Field(default=0.0, ge=0)

    # Delivery tracking
    is_return: bool = False
    original_delivery_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None

    # Audit
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related entities
    recipient: Optional[RecipientSchema] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response"""

    total: int
    items: list[OrderResponse]


class AssignOrderRequest(BaseModel):
    """Assign order request"""

    courier_id: UUID = Field(..., description="Courier ID")
    shift_id: UUID = Field(..., description="Shift ID")

    class Config:
        json_schema_extra = {
            "example": {
                "courier_id": "550e8400-e29b-41d4-a716-446655440000",
                "shift_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }


class MarkDeliveredRequest(BaseModel):
    """Mark delivered request"""

    delivery_date: Optional[datetime] = Field(None, description="Actual delivery date")

    class Config:
        json_schema_extra = {"example": {"delivery_date": "2024-01-15T14:30:00"}}


class BulkStatusUpdateRequest(BaseModel):
    """Bulk status update request"""

    order_ids: list[UUID] = Field(..., description="List of order IDs")
    status: OrderStatusTypes = Field(..., description="New status")

    class Config:
        json_schema_extra = {
            "example": {
                "order_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001",
                ],
                "status": "IN_TRANSIT",
            }
        }


class PostponeOrdersRequest(BaseModel):
    """Postpone orders request"""

    terminal_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    order_ids: list[UUID] = Field(..., description="List of order IDs")
    new_delivery_date: date = Field(..., description="New delivery date")

    class Config:
        json_schema_extra = {
            "example": {
                "terminal_id": "550e8400-e29b-41d4-a716-446655440000",
                "shift_id": "550e8400-e29b-41d4-a716-446655440001",
                "order_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001",
                ],
                "new_delivery_date": "2024-01-15",
            }
        }
