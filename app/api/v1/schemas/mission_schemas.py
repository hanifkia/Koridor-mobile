"""
Order request/response schemas
"""

from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime, time, date
from typing import Optional

from app.core.entities import MissionStatusType, MissionPostponedType
from app.api.v1.schemas.order_schemas import (
    CoordinatesSchema,
    AddressSchema,
)  # TODO: it is better to have a shared schema and import from there


class MissionResponse(BaseModel):
    id: UUID
    route_id: UUID
    order_id: UUID
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    status: MissionStatusType
    postponed: MissionPostponedType | None = None
    is_return: bool = False

    location: Optional[CoordinatesSchema] = None
    address: Optional[AddressSchema] = None

    arrival_time: Optional[time] = None
    cumulative_duration: Optional[int] = None
    cumulative_distance: Optional[int] = None
    service_time: Optional[int] = None

    actual_arrival_time: Optional[time] = None
    actual_cumulative_duration: Optional[int] = None
    actual_cumulative_distance: Optional[int] = None
    actual_service_time: Optional[int] = None
    actual_mission_start_time: Optional[time] = None
    actual_mission_finish_time: Optional[time] = None

    position_in_route: Optional[int] = None
    waiting_time: Optional[int] = None
    actual_waiting_time: Optional[int] = None

    loading_scan_parcel_time: Optional[datetime] = None
    delivery_scan_parcel_time: Optional[datetime] = None
    delivery_scan_parcel_barcode: Optional[str] = None

    courier_comment: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
