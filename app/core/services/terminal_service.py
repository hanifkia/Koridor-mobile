# app/core/services/terminal_service.py
"""
Terminal/Hub service implementation
"""
from typing import Optional, List
import logging
from uuid import UUID, uuid4
from datetime import timedelta

from app.core.entities import Hub, UserStatus
from app.core.interfaces import IHubRepository, IUserRepository, ICourierRepository

logger = logging.getLogger(__name__)


class TerminalService:
    """Service for terminal/hub operations"""

    def __init__(
        self,
        hub_repo: IHubRepository,
        user_repo: IUserRepository,
        courier_repo: ICourierRepository,
    ):
        self.hub_repo = hub_repo
        self.user_repo = user_repo
        self.courier_repo = courier_repo

    async def setup_terminal(
        self,
        user_id: UUID,
        terminal_name: str,
        latitude: float,
        longitude: float,
        address: Optional[str] = None,
        setup_time: Optional[int] = 15,
        service_time: Optional[int] = 30,
        return_to_hub: bool = True,
    ) -> Hub:
        """
        Setup terminal for a courier

        **Validation:**
        1. Verify user exists
        2. Fetch courier
        3. Create hub
        4. Activate user

        **Returns:**
        - Created hub entity

        **Raises:**
        - ValueError: If user or courier not found
        - Exception: If hub creation fails
        """
        logger.info(f"🔄 Setting up terminal for user: {user_id}")

        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            raise ValueError(f"User not found: {user_id}")

        logger.info(f"✅ User verified: {user.email}")

        # Fetch courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Create hub
        try:
            logger.info(f"🔄 Creating hub: {terminal_name}")

            setup_time_delta = (
                timedelta(minutes=setup_time) if setup_time else timedelta(minutes=15)
            )
            service_time_delta = (
                timedelta(minutes=service_time)
                if service_time
                else timedelta(minutes=30)
            )

            hub = Hub(
                id=uuid4(),
                courier_id=courier.id,
                name=terminal_name,
                lat=latitude,
                lon=longitude,
                address=address or "",
                setup_time=setup_time_delta,
                service_time=service_time_delta,
                return_to_hub=return_to_hub,
            )

            created_hub = await self.hub_repo.create(hub)
            logger.info(f"✅ Hub created: {created_hub.id}")

            # Activate user
            await self.user_repo.update_status(user_id, UserStatus.ACTIVE)
            logger.info(f"✅ User activated")

            user.is_terminal_setup_completed = True
            await self.user_repo.update(user_id, user)
            logger.info(f"✅ User terminal setup marked as completed")

            return created_hub

        except Exception as e:
            logger.error(f"❌ Error creating hub: {str(e)}", exc_info=True)
            raise

    async def update_terminal(
        self,
        user_id: UUID,
        terminal_id: UUID,
        terminal_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        setup_time: Optional[int] = None,
        service_time: Optional[int] = None,
        return_to_hub: Optional[bool] = None,
    ) -> Hub:
        """
        Update terminal details

        **Validation:**
        1. Verify hub exists
        2. Verify hub belongs to user's courier
        3. Update hub

        **Returns:**
        - Updated hub entity

        **Raises:**
        - ValueError: If hub not found or unauthorized
        - Exception: If update fails
        """
        logger.info(f"🔄 Updating terminal: {terminal_id}")

        # Fetch hub
        hub = await self.hub_repo.get_by_id(terminal_id)
        if not hub:
            logger.error(f"❌ Hub not found: {terminal_id}")
            raise ValueError(f"Hub not found: {terminal_id}")

        # Verify hub belongs to user's courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier or hub.courier_id != courier.id:
            logger.error(f"❌ Unauthorized update for hub: {terminal_id}")
            raise ValueError("Not authorized to update this hub")

        logger.info(f"✅ Authorization verified")

        # Update hub
        try:
            hub.name = terminal_name or hub.name
            hub.lat = latitude or hub.lat
            hub.lon = longitude or hub.lon
            hub.address = address or hub.address

            if setup_time:
                hub.setup_time = timedelta(minutes=setup_time)
            if service_time:
                hub.service_time = timedelta(minutes=service_time)
            if return_to_hub is not None:
                hub.return_to_hub = return_to_hub

            updated_hub = await self.hub_repo.update(terminal_id, hub)
            logger.info(f"✅ Hub updated: {terminal_id}")

            return updated_hub

        except Exception as e:
            logger.error(f"❌ Error updating hub: {str(e)}", exc_info=True)
            raise

    async def get_user_terminals(self, user_id: UUID) -> List[Hub]:
        """
        Get all terminals for a user's courier

        **Returns:**
        - List of hub entities

        **Raises:**
        - ValueError: If courier not found
        """
        logger.info(f"🔄 Getting terminals for user: {user_id}")

        # Fetch courier
        courier = await self.courier_repo.get_by_user_id(user_id)
        if not courier:
            logger.error(f"❌ Courier not found for user: {user_id}")
            raise ValueError(f"Courier not found for user: {user_id}")

        logger.info(f"✅ Courier found: {courier.id}")

        # Fetch terminals
        terminals = await self.hub_repo.get_by_courier_id(courier.id)
        logger.info(f"✅ Retrieved {len(terminals)} terminals")

        return terminals

    async def get_terminal(self, terminal_id: UUID) -> Hub:
        """
        Get a specific terminal

        **Returns:**
        - Hub entity

        **Raises:**
        - ValueError: If hub not found
        """
        logger.info(f"🔄 Getting terminal: {terminal_id}")

        hub = await self.hub_repo.get_by_id(terminal_id)
        if not hub:
            logger.error(f"❌ Hub not found: {terminal_id}")
            raise ValueError(f"Hub not found: {terminal_id}")

        logger.info(f"✅ Terminal retrieved: {terminal_id}")
        return hub
