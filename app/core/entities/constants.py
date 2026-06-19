from enum import Enum
from dataclasses import dataclass
from datetime import timedelta
from ._enums import FuelType


@dataclass
class VehicleConstants:
    weight_capacity: float
    volume_capacity: float
    loading_cost: float
    travel_cost_per_km: float
    travel_cost_per_hour: float
    loading_time: timedelta
    average_speed: int
    max_duration: timedelta
    fuel_consumption_per_100_km: int
    fuel_type: FuelType
    max_tasks: int


class VehicleDefaultConstants(Enum):
    BIKE = VehicleConstants(
        weight_capacity=1.0,
        volume_capacity=0.0,
        loading_cost=0.0,
        travel_cost_per_km=0.0,
        travel_cost_per_hour=0.0,
        loading_time=timedelta(seconds=0),
        average_speed=0,
        max_duration=timedelta(seconds=0),
        fuel_consumption_per_100_km=0,
        fuel_type=FuelType.PETROL,
        max_tasks=0,
    )

    CAR = VehicleConstants(
        weight_capacity=1.0,
        volume_capacity=0.0,
        loading_cost=0.0,
        travel_cost_per_km=0.0,
        travel_cost_per_hour=0.0,
        loading_time=timedelta(seconds=0),
        average_speed=0,
        max_duration=timedelta(seconds=0),
        fuel_consumption_per_100_km=0,
        fuel_type=FuelType.PETROL,
        max_tasks=0,
    )
    VAN = VehicleConstants(
        weight_capacity=1.0,
        volume_capacity=0.0,
        loading_cost=0.0,
        travel_cost_per_km=0.0,
        travel_cost_per_hour=0.0,
        loading_time=timedelta(seconds=0),
        average_speed=0,
        max_duration=timedelta(seconds=0),
        fuel_consumption_per_100_km=0,
        fuel_type=FuelType.PETROL,
        max_tasks=0,
    )
    TRUCK = VehicleConstants(
        weight_capacity=1.0,
        volume_capacity=0.0,
        loading_cost=0.0,
        travel_cost_per_km=0.0,
        travel_cost_per_hour=0.0,
        loading_time=timedelta(seconds=0),
        average_speed=0,
        max_duration=timedelta(seconds=0),
        fuel_consumption_per_100_km=0,
        fuel_type=FuelType.PETROL,
        max_tasks=0,
    )
    TRAILER = VehicleConstants(
        weight_capacity=1.0,
        volume_capacity=0.0,
        loading_cost=0.0,
        travel_cost_per_km=0.0,
        travel_cost_per_hour=0.0,
        loading_time=timedelta(seconds=0),
        average_speed=0,
        max_duration=timedelta(seconds=0),
        fuel_consumption_per_100_km=0,
        fuel_type=FuelType.PETROL,
        max_tasks=0,
    )
