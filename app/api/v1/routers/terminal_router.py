# app/api/v1/routers/terminal_router.py
"""
Terminal router with service layer
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import logging

from app.api.v1.schemas.terminal_schemas import (
    TerminalCreateSchema,
    TerminalUpdateSchema,
    TerminalResponseSchema,
)
from app.core.entities import Hub
from app.core.services.terminal_service import TerminalService
from app.config.dependencies import (
    get_terminal_service,
)
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/terminal", tags=["Terminal"])
logger = logging.getLogger(__name__)


@router.post(
    "/setup", status_code=status.HTTP_201_CREATED, response_model=TerminalResponseSchema
)
async def setup_terminal(
    request: TerminalCreateSchema,
    terminal_service: TerminalService = Depends(get_terminal_service),
    current_user: dict = Depends(get_current_user),
):
    """Setup terminal for courier"""

    try:
        hub: Hub = await terminal_service.setup_terminal(
            user_id=current_user.get("user_id"),
            terminal_name=request.terminal_name,
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            setup_time=request.setup_time,
            service_time=request.service_time,
            return_to_hub=request.return_to_hub,
        )
        logger.info(f"✅ Terminal created: {hub.id}")
        return TerminalResponseSchema.from_orm(hub)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup terminal",
        )


@router.patch(
    "/update/{terminal_id}",
    status_code=status.HTTP_200_OK,
    response_model=TerminalResponseSchema,
)
async def update_terminal(
    terminal_id: UUID,
    request: TerminalUpdateSchema,
    terminal_service: TerminalService = Depends(get_terminal_service),
    current_user: dict = Depends(get_current_user),
):
    """Update terminal details"""

    try:
        hub: Hub = await terminal_service.update_terminal(
            user_id=current_user.get("user_id"),
            terminal_id=terminal_id,
            terminal_name=request.terminal_name,
            latitude=request.latitude,
            longitude=request.longitude,
            address=request.address,
            setup_time=request.setup_time,
            service_time=request.service_time,
            return_to_hub=request.return_to_hub,
        )
        logger.info(f"✅ Terminal updated: {hub.id}")
        return TerminalResponseSchema.from_orm(hub)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update terminal",
        )


@router.get(
    "/all", status_code=status.HTTP_200_OK, response_model=list[TerminalResponseSchema]
)
async def get_courier_all_terminals(
    terminal_service: TerminalService = Depends(get_terminal_service),
    current_user: dict = Depends(get_current_user),
):
    """Get all terminals for user"""

    try:
        terminals: List[Hub] = await terminal_service.get_user_terminals(
            current_user.get("user_id")
        )
        return [TerminalResponseSchema.from_orm(terminal) for terminal in terminals]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{terminal_id}",
    status_code=status.HTTP_200_OK,
    response_model=TerminalResponseSchema,
)
async def get_terminal(
    terminal_id: UUID,
    terminal_service: TerminalService = Depends(get_terminal_service),
    current_user: dict = Depends(get_current_user),
):
    """Get specific terminal"""

    try:
        terminal: Hub = await terminal_service.get_terminal(terminal_id)
        return TerminalResponseSchema.from_orm(terminal)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
