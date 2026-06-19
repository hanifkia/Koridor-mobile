from uuid import UUID
from pydantic import BaseModel, model_validator
from app.core.entities import CourierStatesType, UndeliveredMissionStatus


class SetCourierStateRequestSchema(BaseModel):
    state: CourierStatesType
    undeliver_type: UndeliveredMissionStatus | None = None
    route_id: UUID
    order_id: UUID = None
    comment: str | None = None

    @model_validator(mode="after")
    @classmethod
    def fields_validation(cls, values):
        if (
            values.state
            in (
                CourierStatesType.STARTLOADING,
                CourierStatesType.ARRIVEDATDELIVERY,
                CourierStatesType.DELIVERED,
                CourierStatesType.UNDELIVERED,
                CourierStatesType.STARTNEXTDELIVERY,
                CourierStatesType.RETURNTOHUB,
            )
            and values.order_id is None
        ):
            raise ValueError("order_id is required.")
        if (
            values.state == CourierStatesType.UNDELIVERED
            and values.undeliver_type is None
        ):
            raise ValueError("undeliver_type is required.")
        return values


class StartRouteSelfManagedSchema(BaseModel):
    route_id: UUID
    sorted_order_ids: list[UUID]
