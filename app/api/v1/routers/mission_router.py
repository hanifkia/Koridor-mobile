"""
Mission router with service layer
"""

import logging
import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_filter import FilterDepends

from app.api.v1.schemas.mission_schemas import MissionResponse
from app.api.v1.schemas._shared import PaginatedResponse
from app.adapters.filters.mission_filter import MissionFilter
from app.core.services.mission_service import MissionService
from app.core.services.mission_response_mapper import (
    map_missions_to_responses,
    map_mission_to_response,
)
from app.config.dependencies import get_mission_service
from app.config.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mission", tags=["Missions"])


@router.get(
    "/",
    response_model=PaginatedResponse[MissionResponse],
    status_code=status.HTTP_200_OK,
)
async def list_courier_missions(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100),
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[MissionResponse]:
    """
    Get all courier missions with pagination

    **Query Parameters:**
    - page: Page number (1-indexed, default: 1)
    - limit: Maximum number of records to return (default: 10, max: 100)

    **Returns:**
    - List of MissionResponse objects for the current user's courier

    **Raises:**
    - HTTPException: 404 if courier not found
    - HTTPException: 500 if database query fails
    """

    try:
        skip = (page - 1) * limit
        user_id = current_user["user_id"]

        missions, total_count = await mission_service.get_courier_missions(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        logger.info(f"✅ Retrieved {len(missions)} missions for user: {user_id}")

        return PaginatedResponse[MissionResponse](
            data=map_missions_to_responses(missions),
            total_count=total_count,
            total_pages=math.ceil(total_count / limit) if total_count > 0 else 1,
            current_page=page,
            per_page=limit,
            has_next=page < math.ceil(total_count / limit) if total_count > 0 else 1,
            has_previous=page > 1,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to list missions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve missions",
        )


@router.get(
    "/{mission_id}",
    response_model=MissionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_mission_by_id(
    mission_id: UUID,
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> MissionResponse:
    """
    Get a specific mission by ID

    **Path Parameters:**
    - mission_id: The mission ID to retrieve

    **Returns:**
    - MissionResponse object

    **Raises:**
    - HTTPException: 404 if mission not found or doesn't belong to user
    - HTTPException: 500 if database query fails
    """

    try:
        user_id = current_user["user_id"]

        # Verify mission ownership and get mission
        mission = await mission_service.verify_mission_ownership(
            user_id=user_id,
            mission_id=mission_id,
        )
        logger.info(f"✅ Retrieved mission: {mission_id}")

        return map_mission_to_response(mission)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to get mission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mission",
        )


@router.get(
    "/courier/{user_id}/pending",
    response_model=list[MissionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_pending_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> list[MissionResponse]:
    """
    Get all pending missions for current courier

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 10, max: 100)

    **Returns:**
    - List of MissionResponse objects with PENDING status

    **Raises:**
    - HTTPException: 404 if courier not found
    - HTTPException: 500 if database query fails
    """

    try:
        user_id = current_user["user_id"]

        # Get courier first
        from app.core.services.mission_service import MissionService

        courier = await mission_service.courier_repo.get_by_user_id(user_id)
        if not courier:
            raise ValueError(f"Courier not found for user: {user_id}")

        missions = await mission_service.get_pending_missions(
            courier_id=courier.id,
            skip=skip,
            limit=limit,
        )
        logger.info(
            f"✅ Retrieved {len(missions)} pending missions for user: {user_id}"
        )

        return map_missions_to_responses(missions)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to list pending missions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending missions",
        )


@router.get(
    "/courier/{user_id}/completed",
    response_model=list[MissionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_completed_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> list[MissionResponse]:
    """
    Get all completed missions for current courier

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 10, max: 100)

    **Returns:**
    - List of MissionResponse objects with COMPLETED status

    **Raises:**
    - HTTPException: 404 if courier not found
    - HTTPException: 500 if database query fails
    """

    try:
        user_id = current_user["user_id"]

        # Get courier first
        courier = await mission_service.courier_repo.get_by_user_id(user_id)
        if not courier:
            raise ValueError(f"Courier not found for user: {user_id}")

        missions = await mission_service.get_completed_missions(
            courier_id=courier.id,
            skip=skip,
            limit=limit,
        )
        logger.info(
            f"✅ Retrieved {len(missions)} completed missions for user: {user_id}"
        )

        return map_missions_to_responses(missions)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Failed to list completed missions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve completed missions",
        )


@router.get(
    "/route/{route_id}",
    response_model=list[MissionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_missions_by_route(
    route_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> list[MissionResponse]:
    """
    Get all missions for a specific route

    **Path Parameters:**
    - route_id: The route ID to retrieve missions for

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100, max: 500)

    **Returns:**
    - List of MissionResponse objects for the route

    **Raises:**
    - HTTPException: 500 if database query fails
    """

    try:
        missions = await mission_service.get_missions_by_route(
            route_id=route_id,
            skip=skip,
            limit=limit,
        )
        logger.info(f"✅ Retrieved {len(missions)} missions for route: {route_id}")

        return map_missions_to_responses(missions)

    except Exception as e:
        logger.error(f"❌ Failed to list missions by route: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve missions",
        )


@router.get(
    "/hub/{terminal_id}",
    response_model=list[MissionResponse],
    status_code=status.HTTP_200_OK,
)
async def get_missions_by_hub(
    terminal_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    mission_service: MissionService = Depends(get_mission_service),
    current_user: dict = Depends(get_current_user),
) -> list[MissionResponse]:
    """
    Get all missions for a specific hub (admin only)

    **Path Parameters:**
    - terminal_id: The hub ID to retrieve missions for

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100, max: 500)

    **Returns:**
    - List of MissionResponse objects for the hub

    **Raises:**
    - HTTPException: 500 if database query fails
    """

    try:
        missions = await mission_service.get_missions_by_hub(
            terminal_id=terminal_id,
            skip=skip,
            limit=limit,
        )
        logger.info(f"✅ Retrieved {len(missions)} missions for hub: {terminal_id}")

        return map_missions_to_responses(missions)

    except Exception as e:
        logger.error(f"❌ Failed to list missions by hub: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve missions",
        )
