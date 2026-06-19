import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.states_schemas import (
    SetCourierStateRequestSchema,
    StartRouteSelfManagedSchema,
)

from app.core.entities import (
    CourierCurrentState,
    CourierStatesType,
)
from app.config.dependencies import (
    get_courier_current_state_repository,
    get_courier_repository,
    get_courier_state_service,
)
from app.config.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/states", tags=["States"])


@router.post("/init", status_code=status.HTTP_201_CREATED)
async def init_courier_operations(
    current_user=Depends(get_current_user),
    courier_repo=Depends(get_courier_repository),
    current_state_repo=Depends(get_courier_current_state_repository),
):
    # TODO: this is a test endpoint actually. init should happened when courier is created
    user_id = current_user["user_id"]

    courier = await courier_repo.get_by_user_id(user_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier not found",
        )

    current_state = current_state_repo.get_by_courier_id(courier.id)
    if current_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Courier current state already exists",
        )

    current_state = CourierCurrentState(
        courier_id=courier.id,
        state=CourierStatesType.IDLE,
    )
    current_state = await current_state_repo.create(current_state)
    logger.info(
        f"✅ Courier current state created: {current_state.id} for courier: {courier.id}"
    )
    return current_state


@router.get("/current_state", status_code=status.HTTP_200_OK)
async def get_courier_current_state(
    courier_id: UUID,
    courier_repo=Depends(get_courier_repository),
    current_state_repo=Depends(get_courier_current_state_repository),
    current_user=Depends(get_current_user),
):
    user_id = current_user["user_id"]

    courier = await courier_repo.get_by_user_id(user_id)
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier not found",
        )

    current_state = await current_state_repo.get_by_courier_id(courier_id)
    if not current_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier current state not found",
        )

    return current_state


@router.put("/set_state", status_code=status.HTTP_200_OK)
async def set_courier_state(
    request: SetCourierStateRequestSchema,
    current_user: dict = Depends(get_current_user),
    courier_state_service=Depends(get_courier_state_service),
) -> dict:
    """
    Update courier state and handle mission status transitions.

    **State Transitions:**
    - ARRIVEDATHUB: Courier arrived at hub
    - STARTLOADING: Start loading packages
    - STARTROUTE: Start route with first mission
    - ARRIVEDATDELIVERY: Arrived at delivery location
    - DELIVERED: Order successfully delivered
    - UNDELIVERED: Order not delivered (requires undeliver_type)
    - STARTNEXTDELIVERY: Move to next mission
    - RETURNTOHUB: Return to hub
    - FINISHROUTE: Route completed
    """

    user_id = current_user["user_id"]
    try:
        result = await courier_state_service.set_courier_state(user_id, request)
        return result

    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error updating courier state: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update courier state",
        )


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_route(
    data: StartRouteSelfManagedSchema,
    current_user: dict = Depends(get_current_user),
    courier_state_service=Depends(get_courier_state_service),
):
    """Start route with self-managed loading"""

    try:
        result = await courier_state_service.start_route_self_managed(
            user_id=current_user["user_id"],
            route_id=data.route_id,
            sorted_order_ids=data.sorted_order_ids,
        )
        return result

    except ValueError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error starting self-managed route: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start route",
        )
