"""
Route filter for advanced filtering
"""

from __future__ import annotations

from datetime import datetime, date, time
from typing import Optional
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.adapters.database.models import RouteORM, CourierORM, HubORM
from app.core.entities import RouteStatesType


class RouteFilter(Filter):
    """Advanced route filter with search capabilities"""

    # ID Filters
    terminal_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    courier_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None

    # Status Filter
    status: Optional[RouteStatesType] = None

    # Date Filters
    created_at__gte: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    # Time Filters
    start_time__gte: Optional[time] = None
    start_time__lte: Optional[time] = None

    # Numeric Filters
    duration__gte: Optional[int] = None
    duration__lte: Optional[int] = None
    distance__gte: Optional[int] = None
    distance__lte: Optional[int] = None

    # Boolean Filters
    must_return: Optional[bool] = None
    lock: Optional[bool] = None

    # Search Filter
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = RouteORM
        search_field_name = "search"
        search_model_fields = ["route_name"]

    def filter(self, query: Select) -> Select:
        """
        Apply filters to query

        Args:
            query: SQLAlchemy select query

        Returns:
            Filtered query
        """
        # Temporarily disable search to let super() handle standard filters
        search_value = self.search
        self.search = None

        # Apply all standard filters
        query = super().filter(query)

        # Restore search value
        self.search = search_value

        # Apply custom cross-model search if provided
        if search_value:
            term = f"%{search_value}%"
            query = (
                query.outerjoin(CourierORM)
                .outerjoin(HubORM)
                .where(
                    or_(
                        RouteORM.route_name.ilike(term),
                        CourierORM.first_name.ilike(term),
                        CourierORM.last_name.ilike(term),
                        HubORM.name.ilike(term),
                    )
                )
            )

        return query

    class Config:
        """Pydantic config"""

        from_attributes = True
