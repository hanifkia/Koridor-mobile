"""
Mission filter for advanced filtering
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.adapters.database.models import MissionORM, OrderORM, CourierORM
from app.core.entities import MissionStatusType


class MissionFilter(Filter):
    """Advanced mission filter with search capabilities"""

    # ID Filters
    route_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    terminal_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    courier_id: Optional[UUID] = None

    # Status Filter
    status: Optional[MissionStatusType] = None

    # Boolean Filters
    is_return: Optional[bool] = None

    # Search Filter
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = MissionORM
        search_field_name = "search"
        search_model_fields = ["delivery_scan_parcel_barcode", "courier_comment"]

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
                query.outerjoin(OrderORM)
                .outerjoin(CourierORM)
                .where(
                    or_(
                        MissionORM.delivery_scan_parcel_barcode.ilike(term),
                        MissionORM.courier_comment.ilike(term),
                        OrderORM.barcode.ilike(term),
                        CourierORM.first_name.ilike(term),
                        CourierORM.last_name.ilike(term),
                    )
                )
            )

        return query

    class Config:
        """Pydantic config"""

        from_attributes = True
