# app/api/v1/routers/terminal_router.py
"""
Terminal router with service layer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import logging
from typing import List

from app.api.v1.schemas.terminal_schemas import (
    ShiftCreateSchema,
    ShiftResponseSchema,
)
from app.api.v1.schemas.hub_shift_response import HubShiftResponseSchema
from app.core.entities import HubShifts
from app.core.services.shift_service import ShiftService
from app.config.dependencies import (
    get_shift_service,
)
from app.config.security import get_current_user

router = APIRouter(prefix="/api/v1/shifts", tags=["Shifts"])
logger = logging.getLogger(__name__)


@router.post(
    "/shifts/{terminal_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=ShiftResponseSchema,
)
async def create_shift(
    terminal_id: UUID,
    request: ShiftCreateSchema,
    shift_service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user),
):
    """Create shift for hub"""
    try:
        shift: HubShifts = await shift_service.create_shift(
            user_id=current_user.get("user_id"),
            terminal_id=terminal_id,
            start_time=request.start_time,
            finish_time=request.finish_time,
        )
        logger.info(f"✅ Shift created: {shift.id}")
        return ShiftResponseSchema(
            id=str(shift.id),
            terminal_id=str(shift.terminal_id),
            start_time=shift.start_time,
            finish_time=shift.finish_time,
            created_at=shift.created_at.isoformat() if shift.created_at else None,
        )

    except ValueError as e:
        error_detail = str(e)
        if isinstance(e.args[0], dict):
            error_detail = e.args[0]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
        )
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shift",
        )


@router.get(
    "/shifts/{terminal_id}",
    status_code=status.HTTP_200_OK,
    response_model=HubShiftResponseSchema,
)
async def get_hub_shifts(
    terminal_id: UUID,
    shift_service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user),
):
    """Get shifts for hub"""

    try:
        shifts: List[HubShifts] = await shift_service.get_hub_shifts(terminal_id)
        logger.info(f"✅ Retrieved {len(shifts)} shifts")
        return HubShiftResponseSchema(
            terminal_id=str(terminal_id),
            shifts_count=len(shifts),
            shifts=[
                ShiftResponseSchema(
                    id=str(shift.id),
                    terminal_id=str(shift.terminal_id),
                    start_time=shift.start_time,
                    finish_time=shift.finish_time,
                    created_at=(
                        shift.created_at.isoformat() if shift.created_at else None
                    ),
                )
                for shift in shifts
            ],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get shifts",
        )


@router.patch(
    "/shifts/{shift_id}",
    status_code=status.HTTP_200_OK,
    response_model=ShiftResponseSchema,
)
async def update_shift(
    shift_id: UUID,
    request: ShiftCreateSchema,
    shift_service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user),
):
    """Update shift"""

    try:
        shift: HubShifts = await shift_service.update_shift(
            user_id=current_user.get("user_id"),
            shift_id=shift_id,
            start_time=request.start_time,
            finish_time=request.finish_time,
        )
        logger.info(f"✅ Shift updated: {shift.id}")
        return ShiftResponseSchema(
            id=str(shift.id),
            terminal_id=str(shift.terminal_id),
            start_time=shift.start_time,
            finish_time=shift.finish_time,
            created_at=shift.created_at.isoformat() if shift.created_at else None,
        )

    except ValueError as e:
        error_detail = str(e)
        if isinstance(e.args[0], dict):
            error_detail = e.args[0]
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_detail,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail,
        )


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    shift_service: ShiftService = Depends(get_shift_service),
    current_user: dict = Depends(get_current_user),
):
    """Delete shift"""
    try:
        await shift_service.delete_shift(shift_id)
        logger.info(f"✅ Shift deleted: {shift_id}")
        return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
