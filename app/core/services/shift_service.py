# app/core/services/shift_service.py
"""
Shift service implementation
"""
from typing import Optional, List
import logging
from uuid import UUID, uuid4
from datetime import time

from app.core.entities import HubShifts
from app.core.interfaces import (
    IHubShiftRepository,
    IHubRepository,
    ICourierRepository,
    IUserRepository,
)

logger = logging.getLogger(__name__)


class ShiftService:
    """Service for hub shift operations"""

    def __init__(
        self,
        shift_repo: IHubShiftRepository,
        hub_repo: IHubRepository,
        courier_repo: ICourierRepository,
        user_repo: IUserRepository,
    ):
        self.shift_repo = shift_repo
        self.hub_repo = hub_repo
        self.courier_repo = courier_repo
        self.user_repo = user_repo

    async def create_shift(
        self,
        user_id: UUID,
        terminal_id: UUID,
        start_time: time,
        finish_time: time,
    ) -> HubShifts:
        """
        Create a new shift for a hub

        **Validation:**
        1. Verify user and hub exist
        2. Verify hub belongs to user's courier
        3. Check for time overlaps
        4. Create shift

        **Returns:**
        - Created shift entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If creation fails
        """
        logger.info(f"🔄 Creating shift for hub: {terminal_id}, user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User verified: {user.email}")

        # Verify hub exists
        hub = await self.hub_repo.get_by_id(terminal_id)
        if not hub:
            logger.error(f"❌ Hub not found: {terminal_id}")
            raise ValueError(f"Hub not found: {terminal_id}")

        logger.info(f"✅ Hub verified: {hub.id}")

        # Verify hub belongs to user's courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier or hub.courier_id != courier.id:
            logger.error(f"❌ Hub {terminal_id} does not belong to user {user_id}")
            raise ValueError("Hub does not belong to your courier")

        logger.info(f"✅ Hub ownership verified")

        # Check for overlaps
        logger.info(f"🔍 Checking for overlapping shifts")

        overlapping_shift = await self.shift_repo.check_shift_overlap(
            terminal_id=terminal_id,
            start_time=start_time,
            finish_time=finish_time,
        )

        if overlapping_shift:
            logger.warning(f"⚠️  Overlap detected with shift: {overlapping_shift.id}")

            overlap_type = self.shift_repo._get_overlap_type(
                start_time,
                finish_time,
                overlapping_shift.start_time,
                overlapping_shift.finish_time,
            )

            raise ValueError(
                {
                    "error": "Shift time conflicts with existing shift",
                    "existing_shift_id": str(overlapping_shift.id),
                    "existing_start_time": str(overlapping_shift.start_time),
                    "existing_finish_time": str(overlapping_shift.finish_time),
                    "new_start_time": str(start_time),
                    "new_finish_time": str(finish_time),
                    "overlap_type": overlap_type,
                }
            )

        logger.info(f"✅ No overlaps detected")

        # Create shift
        try:
            logger.info(f"🔄 Creating shift: {start_time}-{finish_time}")

            shift = HubShifts(
                id=uuid4(),
                terminal_id=terminal_id,
                start_time=start_time,
                finish_time=finish_time,
            )

            created_shift = await self.shift_repo.create(shift)
            logger.info(f"✅ Shift created: {created_shift.id}")

            return created_shift

        except Exception as e:
            logger.error(f"❌ Error creating shift: {str(e)}", exc_info=True)
            raise

    async def update_shift(
        self,
        user_id: UUID,
        shift_id: UUID,
        start_time: time,
        finish_time: time,
    ) -> HubShifts:
        """
        Update an existing shift

        **Validation:**
        1. Verify shift exists
        2. Check for overlaps (excluding current shift)
        3. Update shift

        **Returns:**
        - Updated shift entity

        **Raises:**
        - ValueError: If validation fails
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating shift: {shift_id}")

        # Get existing shift
        existing_shift = await self.shift_repo.get_by_id(shift_id)
        if not existing_shift:
            logger.error(f"❌ Shift not found: {shift_id}")
            raise ValueError(f"Shift not found: {shift_id}")

        logger.info(f"✅ Shift found: {shift_id}")

        # Check for overlaps (excluding this shift)
        logger.info(f"🔍 Checking for overlapping shifts")

        overlapping_shift = await self.shift_repo.check_shift_overlap(
            terminal_id=existing_shift.terminal_id,
            start_time=start_time,
            finish_time=finish_time,
            exclude_shift_id=shift_id,
        )

        if overlapping_shift:
            logger.warning(
                f"⚠️  Update would conflict with shift: {overlapping_shift.id}"
            )
            raise ValueError(
                {
                    "error": "Updated shift time conflicts with existing shift",
                    "existing_shift_id": str(overlapping_shift.id),
                    "existing_start_time": str(overlapping_shift.start_time),
                    "existing_finish_time": str(overlapping_shift.finish_time),
                }
            )

        logger.info(f"✅ No conflicts detected")

        # Update shift
        try:
            existing_shift.start_time = start_time
            existing_shift.finish_time = finish_time

            updated_shift = await self.shift_repo.update(shift_id, existing_shift)
            logger.info(f"✅ Shift updated: {shift_id}")

            return updated_shift

        except Exception as e:
            logger.error(f"❌ Error updating shift: {str(e)}", exc_info=True)
            raise

    async def delete_shift(self, shift_id: UUID) -> bool:
        """
        Delete a shift

        **Returns:**
        - True if deleted, False otherwise

        **Raises:**
        - Exception: If delete fails
        """
        logger.info(f"🔄 Deleting shift: {shift_id}")

        deleted = await self.shift_repo.delete(shift_id)

        if not deleted:
            logger.error(f"❌ Shift not found: {shift_id}")
            raise ValueError(f"Shift not found: {shift_id}")

        logger.info(f"✅ Shift deleted: {shift_id}")
        return True

    async def get_hub_shifts(self, terminal_id: UUID) -> List[HubShifts]:
        """
        Get all shifts for a hub

        **Returns:**
        - List of shift entities

        **Raises:**
        - ValueError: If hub not found
        """
        logger.info(f"🔄 Getting shifts for hub: {terminal_id}")

        # Verify hub exists
        hub = await self.hub_repo.get_by_id(terminal_id)
        if not hub:
            logger.error(f"❌ Hub not found: {terminal_id}")
            raise ValueError(f"Hub not found: {terminal_id}")

        logger.info(f"✅ Hub verified: {terminal_id}")

        # Fetch shifts
        shifts = await self.shift_repo.get_by_terminal_id(terminal_id)
        logger.info(f"✅ Retrieved {len(shifts)} shifts")

        return shifts
