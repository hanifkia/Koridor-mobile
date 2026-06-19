from abc import ABC, abstractmethod
from uuid import UUID
from typing import List, Optional, Tuple

from app.core.entities import Hub, Vehicle, Route, Order


class ISolverService(ABC):
    @abstractmethod
    async def solve(self, solver_input: dict) -> Optional[List[UUID]]:
        """Generate routes for orders"""
        pass

    @abstractmethod
    async def map_to_solver_input(
        self, orders: Order, hub: Hub, vehicle: Vehicle, params: dict
    ) -> dict:
        """Map params to solver input"""
        pass

    @abstractmethod
    async def map_solver_output(self, params: dict) -> Tuple[Route, list[UUID]]:
        """Get solver output"""
        pass
