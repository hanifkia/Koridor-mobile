from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.entities import HubShifts
from app.core.interfaces.repositories._base import IRepository


class IHubShiftRepository(IRepository[HubShifts]):
    @abstractmethod
    async def get_by_terminal_id(self, terminal_id: UUID) -> Optional[list[HubShifts]]:
        """Get entity by ID"""
        pass
