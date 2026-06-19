import logging
import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas.route_schemas import (
    RouteResponse,
    GenerateRouteRequest,
)
from app.api.v1.schemas.mission_schemas import MissionResponse
from app.api.v1.schemas._shared import PaginatedResponse
from app.core.interfaces.services.solver_service_interface import ISolverService
from app.config.dependencies import get_solver_service
from app.config.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/route", tags=["Routes"])


# ============================================================================
# ROUTE ENDPOINTS
# ============================================================================
class EcosystemException(Exception):
    """Base exception for all ecosystem errors"""

    pass


class RouteException(EcosystemException):
    """Base exception for route-related errors"""

    pass


class RouteServiceError(RouteException):
    """Base exception for RouteService errors"""

    pass


class RouteGenerationError(RouteServiceError):
    """
    Raised when route generation/optimization fails

    This is a recoverable error that indicates the solver couldn't generate
    a valid route for the given orders. Common causes:
    - Orders violate vehicle capacity constraints
    - Orders have incompatible time windows
    - No feasible route exists
    - Solver encountered unsupported location
    - Network connectivity issues with solver API
    """

    pass


@router.post("/generate", response_model=dict, status_code=status.HTTP_200_OK)
async def generate_route(
    request: GenerateRouteRequest,
    current_user: dict = Depends(get_current_user),
    solver_service=Depends(get_solver_service),
):
    """Generate a route for a list of orders"""

    user_id = current_user["user_id"]

    try:
        route = await solver_service.generate_route(
            order_ids=request.order_ids,
            terminal_id=request.terminal_id,
            shift_id=request.shift_id,
            user_id=user_id,
        )

        # ✅ Handle None response (no routes generated)
        if route is None:
            return {
                "success": True,
                "message": "No routes could be generated for the given orders",
                "route": None,
                "reason": "Solver could not optimize any routes (possibly unsupported location or invalid parameters)",
            }

        # ✅ Return successful route
        return {
            "success": True,
            "route_id": str(route.id),
            "missions_count": route.number_of_missions,
            "route": route,
        }

    except RouteGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route generation failed: {str(e)}",
        )


@router.get(
    "/all",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[RouteResponse],
)
async def get_courier_routes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    solver_service=Depends(get_solver_service),
):
    skip = (page - 1) * limit

    routes, total_count = await solver_service.get_courier_all_routes(
        current_user["user_id"], limit, skip
    )
    return PaginatedResponse(
        data=[RouteResponse.from_orm(o) for o in routes],
        total_count=total_count,
        total_pages=math.ceil(total_count / limit) if total_count > 0 else 1,
        current_page=page,
        per_page=limit,
        has_next=page < math.ceil(total_count / limit) if total_count > 0 else 1,
        has_previous=page > 1,
    )


@router.get(
    "/{route_id}",
    status_code=status.HTTP_200_OK,
    response_model=RouteResponse,
)
async def get_route(
    route_id: UUID,
    solver_service=Depends(get_solver_service),
    current_user: dict = Depends(get_current_user),
):

    route = await solver_service.get_route(route_id)
    return RouteResponse.from_orm(route)


@router.get(
    "/{route_id}/missions",
    status_code=status.HTTP_200_OK,
    response_model=list[MissionResponse],
)
async def get_route_missions(
    route_id: UUID,
    solver_service=Depends(get_solver_service),
    current_user: dict = Depends(get_current_user),
):

    missions = await solver_service.get_route_missions(route_id)
    return [MissionResponse.from_orm(m) for m in missions]


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_route(
    route_id: UUID,
    current_user: dict = Depends(get_current_user),
    solver_service: ISolverService = Depends(get_solver_service),
):

    await solver_service.cancel_route(route_id)


@router.get(
    "/assigned/{terminal_id}",
    response_model=RouteResponse,
    status_code=status.HTTP_200_OK,
)
async def get_assigned_route(
    terminal_id: UUID,
    current_user: dict = Depends(get_current_user),
    solver_service=Depends(get_solver_service),
) -> RouteResponse:

    user_id = current_user["user_id"]

    try:
        route = await solver_service.get_current_route(user_id, terminal_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to retrieve assigned route: {str(e)}",
        )

    logger.info(f"DEBUG: Endpoint received route type: {type(route)}")
    logger.info(f"DEBUG: Endpoint route is list? {isinstance(route, list)}")
    logger.info(f"DEBUG: Endpoint route value: {route}")

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assigned route found",
        )

    return RouteResponse.from_orm(route)
