from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum


class TrendRouteStepType(str, Enum):
    START = "start"
    VISIT = "visit"
    END = "end"


class TrendRouteStepModel(BaseModel):
    """Represents a single step within a Trend Route solution."""

    id: str = Field(title="Step Identifier")
    type: TrendRouteStepType = Field(title="Type of The Step")
    longitude: float | None = Field(default=None, title="Longitude")
    latitude: float | None = Field(default=None, title="Latitude")
    stop_id: int | None = Field(default=None, title="Stop ID")
    time_of_arrival: int = Field(title="Arrival Time of the Step")
    cummulated_traveled_time: int = Field(title="Cumulated Traveled Time Upon Step")
    cummulated_traveled_distance: int = Field(
        default=0, title="Cumulated Traveled Distance Upon Step"
    )
    service_time: int = Field(title="Service Time of the Step")
    waiting_time: int = Field(title="Waiting Time of the Step")
    cummulated_load: list[int] | None = Field(
        default=None, title="Vehicle Load After Step Completion"
    )

    model_config = ConfigDict(extra="allow")


class TrendRouteRouteModel(BaseModel):
    """Route-level aggregation returned by Trend Route."""

    id: str = Field(title="Route ID")
    vehicle_id: str = Field(title="Vehicle ID")
    steps: list[TrendRouteStepModel] = Field(title="Route Steps")
    total_cost: int = Field(title="Total Cost")
    total_service_time: int = Field(title="Total Service Time")
    total_traveled_time: int = Field(title="Total Traveled Time")
    total_traveled_distance: int = Field(default=0, title="Total Traveled Distance")
    total_waiting_time: int = Field(title="Total Waiting Time")
    total_number_of_orders: int = Field(title="Total Number of Orders")
    total_number_of_stops: int = Field(title="Total Number of Stops")
    number_of_stops_per_hour: float = Field(title="Number of Stops Per Hour")
    total_duration: int = Field(title="Total Duration of the Route")

    @field_validator("steps", mode="after")
    @classmethod
    def filter_visit_routes(
        cls, steps: list[TrendRouteStepModel]
    ) -> list[TrendRouteStepModel]:
        """Filter steps to keep only those with type 'visit'."""
        return [step for step in steps if step.type == TrendRouteStepType.VISIT.value]

    model_config = ConfigDict(extra="allow")


class TrendRouteOptimizationResponseModel(BaseModel):
    """Full Trend Route optimization response payload."""

    routes: list[TrendRouteRouteModel] = Field(title="Routes")
    unassigned_order_ids: list[str] = Field(
        default_factory=list, title="Unassigned Order IDs"
    )

    model_config = ConfigDict(extra="allow")


class TrendRouteRecalculationResponseModel(BaseModel):
    route: TrendRouteRouteModel = Field(title="Route")

    model_config = ConfigDict(extra="allow")
