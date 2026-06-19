from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrendRouteOrderModel(BaseModel):
    """Order payload expected by the Trend Route optimization service."""

    id: str = Field(title="Task ID of The Order")
    stop_id: int = Field(title="Stop Location ID")
    longitude: float | None = Field(default=None, title="Longitude")
    latitude: float | None = Field(default=None, title="Latitude")
    service_time: int = Field(default=120, title="Order Service Time", ge=0)
    time_windows: list[list[int]] | None = Field(
        default=None,
        title="Order Time Windows",
    )
    weight: int | None = Field(default=0, title="Order Occupying Weight", ge=0)
    volume: int | None = Field(default=0, title="Order Occupying Volume", ge=0)
    is_pickup: bool = Field(default=False, title="Is Order PickUp")
    pickup_id: str | None = Field(default=None, title="Pickup Order ID")

    model_config = ConfigDict(extra="forbid")

    @field_validator("time_windows")
    @classmethod
    def validate_time_windows(
        cls, value: list[list[int]] | None
    ) -> list[list[int]] | None:
        if value is None:
            return value
        for window in value:
            if len(window) != 2:
                raise ValueError("Each time window must contain exactly two integers.")
        return value


class TrendRouteHubModel(BaseModel):
    """Hub payload that anchors the optimization."""

    id: str = Field(default="terminal_id", title="Hub ID")
    longitude: float = Field(title="Longitude")
    latitude: float = Field(title="Latitude")
    is_return_hub: bool = Field(default=False, title="Is Return Hub")

    model_config = ConfigDict(extra="forbid")


class TrendRouteVehicleModel(BaseModel):
    """Vehicle definition used by Trend Route."""

    id: str = Field(default="vehicle_id", title="ID of The Vehicle")
    time_window: list[int] | None = Field(default=None, title="Vehicle Time Window")
    weight_capacity: int | None = Field(default=None, title="Weight Capacity", ge=0)
    volume_capacity: int | None = Field(default=None, title="Volume Capacity", ge=0)
    max_distance: int | None = Field(default=None, title="Maximum Distance", ge=0)
    max_duration: int | None = Field(default=None, title="Maximum Duration", ge=0)
    max_number_orders: int | None = Field(
        default=None, title="Maximum Number of Orders", ge=0
    )
    type: str = Field(default="vehicle_type", title="Vehicle Type")
    ignore_oneway: bool = Field(default=False, title="Ignore Oneway")

    model_config = ConfigDict(extra="forbid")


class TrendRouteOptimizationRequestModel(BaseModel):
    """Top-level request body for Trend Route optimization calls."""

    region_id: str = Field(default="region_id", title="Region ID")
    orders: list[TrendRouteOrderModel] = Field(min_length=2, title="Orders")
    hub: TrendRouteHubModel = Field(title="Hub")
    start_time: int = Field(
        default=0,
        title="Route Start Time",
        description=(
            "The epoch timestamp (or seconds offset) indicating when the route starts. "
            "If 0, ETAs in the response will be relative to the start."
        ),
        ge=0,
    )
    vehicles: list[TrendRouteVehicleModel] | None = Field(
        default=None,
        title="Vehicles",
    )
    max_duration: int | None = Field(
        default=None,
        title="Max Route Duration",
        description="Maximum allowed route duration in seconds.",
        ge=0,
    )
    model_config = ConfigDict(extra="forbid")


class TrendRouteRecalculationRequestModel(BaseModel):
    route_id: str | None = Field(default="route_id", title="Route ID")
    region_id: str | None = Field(default="region_id", title="Region ID")
    courier_id: str | None = Field(default="courier_id", title="Courier ID")
    orders: list[TrendRouteOrderModel] = Field(
        min_length=2,
        title="Orders",
        description="Orders that will be recalculated.",
    )
    hub: TrendRouteHubModel = Field(title="Hub")
    vehicle: TrendRouteVehicleModel | None = Field(
        default=None,
        title="Vehicle",
        description="Vehicle definition used for recalculation.",
    )
    start_time: int | None = Field(
        default=None,
        title="Route Start Time",
        ge=0,
    )
    use_traffic: bool | None = Field(default=False, title="Use Traffic ETAs")
    use_courier_performance_tuning: bool | None = Field(
        default=None,
        title="Use Courier Performance Tuning",
    )
    source_type: str | None = Field(default=None, title="Route Source Type")
    eta_first_stop_fixed: int | None = Field(
        default=None,
        title="ETA First Stop Fixed",
        ge=0,
    )

    model_config = ConfigDict(extra="forbid")
