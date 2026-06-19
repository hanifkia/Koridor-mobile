"""
Mission service implementation
"""

from typing import Optional, List
import logging
from uuid import UUID

from app.core.entities import Mission
from app.core.interfaces import (
    IMissionRepository,
    ICourierRepository,
)

logger = logging.getLogger(__name__)


class MissionService:
    """Service for mission operations"""

    def __init__(
        self,
        mission_repo: IMissionRepository,
        courier_repo: ICourierRepository,
    ):
        self.mission_repo = mission_repo
        self.courier_repo = courier_repo

    async def get_courier_missions(
        self, user_id: UUID, skip: int = 0, limit: int = 10
    ) -> List[Mission]:
        """
        Get all missions for a user's courier

        **Validation:**
        1. Verify courier exists for user
        2. Verify pagination parameters are valid

        **Returns:**
        - List of mission entities

        **Raises:**
        - ValueError: If courier not found
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting missions for user: {user_id} (skip={skip}, limit={limit})"
        )

        # Verify courier exists
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Fetch missions
        try:
            missions = await self.mission_repo.get_by_courier_id(
                courier.id, skip, limit
            )
            logger.info(
                f"✅ Retrieved {len(missions)} missions for courier: {courier.id}"
            )

            total_count = await self.mission_repo.count_by_courier_id(courier.id)
            logger.info(f"✅ Total count: {total_count}")

            return missions, total_count

        except Exception as e:
            logger.error(f"❌ Error getting missions: {str(e)}", exc_info=True)
            raise

    async def get_mission_by_id(self, mission_id: UUID) -> Mission:
        """
        Get mission by ID

        **Validation:**
        1. Verify mission exists

        **Returns:**
        - Mission entity

        **Raises:**
        - ValueError: If mission not found
        """
        logger.info(f"🔄 Getting mission: {mission_id}")

        mission = await self.mission_repo.get_by_id(mission_id)
        if not mission:
            logger.error(f"❌ Mission not found: {mission_id}")
            raise ValueError(f"Mission not found: {mission_id}")

        logger.info(f"✅ Mission found: {mission_id}")
        return mission

    async def verify_mission_ownership(
        self, user_id: UUID, mission_id: UUID
    ) -> Mission:
        """
        Verify that mission belongs to user's courier and return it

        **Validation:**
        1. Verify mission exists
        2. Verify mission belongs to user's courier

        **Returns:**
        - Mission entity

        **Raises:**
        - ValueError: If mission not found or doesn't belong to user
        """
        logger.info(f"🔄 Verifying mission ownership: {mission_id} for user: {user_id}")

        # Get mission
        mission = await self.mission_repo.get_by_id(mission_id)
        if not mission:
            logger.error(f"❌ Mission not found: {mission_id}")
            raise ValueError(f"Mission not found: {mission_id}")

        logger.info(f"✅ Mission found: {mission_id}")

        # Get courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Verify ownership
        if mission.courier_id != courier.id:
            logger.error(
                f"❌ Mission {mission_id} does not belong to courier {courier.id}"
            )
            raise ValueError("Mission does not belong to your courier")

        logger.info(f"✅ Mission ownership verified")
        return mission

    async def get_all_missions(self, skip: int = 0, limit: int = 10) -> List[Mission]:
        """
        Get all missions with pagination (admin only)

        **Returns:**
        - List of mission entities

        **Raises:**
        - Exception: If query fails
        """
        logger.info(f"🔄 Getting all missions (skip={skip}, limit={limit})")

        try:
            missions = await self.mission_repo.get_all(skip=skip, limit=limit)
            logger.info(f"✅ Retrieved {len(missions)} missions")

            return missions

        except Exception as e:
            logger.error(f"❌ Error getting all missions: {str(e)}", exc_info=True)
            raise

    async def get_missions_by_route(
        self, route_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all missions for a specific route

        **Returns:**
        - List of mission entities

        **Raises:**
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting missions for route: {route_id} (skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_route_id(route_id, skip, limit)
            logger.info(f"✅ Retrieved {len(missions)} missions for route: {route_id}")

            return missions

        except Exception as e:
            logger.error(f"❌ Error getting missions by route: {str(e)}", exc_info=True)
            raise

    async def get_missions_by_status(
        self, courier_id: UUID, status: str, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get missions for a courier by status

        **Validation:**
        1. Verify courier exists

        **Returns:**
        - List of mission entities

        **Raises:**
        - ValueError: If courier not found
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting {status} missions for courier: {courier_id} "
            f"(skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_courier_and_status(
                courier_id, status, skip, limit
            )
            logger.info(
                f"✅ Retrieved {len(missions)} {status} missions for courier: {courier_id}"
            )

            return missions

        except Exception as e:
            logger.error(
                f"❌ Error getting missions by status: {str(e)}", exc_info=True
            )
            raise

    async def get_missions_by_hub(
        self, terminal_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all missions for a specific hub

        **Returns:**
        - List of mission entities

        **Raises:**
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting missions for hub: {terminal_id} (skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_terminal_id(
                terminal_id, skip, limit
            )
            logger.info(f"✅ Retrieved {len(missions)} missions for hub: {terminal_id}")

            return missions

        except Exception as e:
            logger.error(f"❌ Error getting missions by hub: {str(e)}", exc_info=True)
            raise

    async def get_pending_missions(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all pending missions for a courier

        **Returns:**
        - List of mission entities with pending status

        **Raises:**
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting pending missions for courier: {courier_id} "
            f"(skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_courier_and_status(
                courier_id, "PENDING", skip, limit
            )
            logger.info(
                f"✅ Retrieved {len(missions)} pending missions for courier: {courier_id}"
            )

            return missions

        except Exception as e:
            logger.error(f"❌ Error getting pending missions: {str(e)}", exc_info=True)
            raise

    async def get_completed_missions(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all completed missions for a courier

        **Returns:**
        - List of mission entities with completed status

        **Raises:**
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting completed missions for courier: {courier_id} "
            f"(skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_courier_and_status(
                courier_id, "COMPLETED", skip, limit
            )
            logger.info(
                f"✅ Retrieved {len(missions)} completed missions for courier: {courier_id}"
            )

            return missions

        except Exception as e:
            logger.error(
                f"❌ Error getting completed missions: {str(e)}", exc_info=True
            )
            raise

    async def get_failed_missions(
        self, courier_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Mission]:
        """
        Get all failed missions for a courier

        **Returns:**
        - List of mission entities with failed status

        **Raises:**
        - Exception: If query fails
        """
        logger.info(
            f"🔄 Getting failed missions for courier: {courier_id} "
            f"(skip={skip}, limit={limit})"
        )

        try:
            missions = await self.mission_repo.get_by_courier_and_status(
                courier_id, "FAILED", skip, limit
            )
            logger.info(
                f"✅ Retrieved {len(missions)} failed missions for courier: {courier_id}"
            )

            return missions

        except Exception as e:
            logger.error(f"❌ Error getting failed missions: {str(e)}", exc_info=True)
            raise
