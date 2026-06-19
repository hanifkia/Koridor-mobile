from uuid import UUID

from pydantic import BaseModel
from decimal import Decimal

from app.core.entities import VehicleType, FuelType


class VehicleUpdateSchema(BaseModel):
    vehicle_type: VehicleType | None = None
    weight_capacity: float | None = None
    volume_capacity: float | None = None
    loading_cost: Decimal | None = None
    travel_cost_per_km: Decimal | None = None
    travel_cost_per_hour: Decimal | None = None
    loading_time: int | None = None
    average_speed: int | None = None
    max_duration: int | None = None
    fuel_consumption_per_100_km: int | None = None
    fuel_type: FuelType | None = None
    max_tasks: int | None = None


class VehicleResponseSchema(BaseModel):
    id: UUID
    vehicle_type: VehicleType
    weight_capacity: float
    volume_capacity: float
    loading_cost: Decimal
    travel_cost_per_km: Decimal
    travel_cost_per_hour: Decimal
    loading_time: int
    average_speed: int
    max_duration: int
    fuel_consumption_per_100_km: int
    fuel_type: FuelType
    max_tasks: int

    class Config:
        from_attributes = True
