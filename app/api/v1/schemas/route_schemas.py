from pydantic import BaseModel, Field, validator
from uuid import UUID
from datetime import datetime, time, date
from typing import Optional

from app.core.entities import RouteCreatedType, RouteStatesType, CostFunctionPlanType


class RouteResponse(BaseModel):
    id: UUID
    terminal_id: UUID
    shift_id: UUID
    courier_id: UUID
    vehicle_id: UUID
    route_name: str
    start_time: time
    finish_time: time
    status: RouteStatesType
    color: str
    must_return: bool
    number_of_missions: int
    created_type: RouteCreatedType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    actual_start_time: Optional[time] = None
    actual_finish_time: Optional[time] = None
    cost: Optional[float] = None
    duration: Optional[int] = None
    distance: Optional[int] = None
    current_mission_id: Optional[UUID] = None
    total_waiting_time: Optional[int] = None
    total_actual_waiting_time: Optional[int] = None
    total_number_of_orders: Optional[int] = None
    total_number_of_stops: Optional[int] = None
    loading_time_start: Optional[datetime] = None
    arrived_at_hub_time: Optional[datetime] = None
    lock: Optional[bool] = None
    modification_time: Optional[time] = None
    courier_score: Optional[int] = None

    class Config:
        from_attributes = True


class GenerateRouteRequest(BaseModel):
    terminal_id: UUID
    shift_id: UUID
    order_ids: list[UUID]
    plan_type: CostFunctionPlanType | None = CostFunctionPlanType.Minimizing_Eco_Routing
