"""
Order filter for advanced filtering
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi_filter.contrib.sqlalchemy import Filter
from sqlalchemy import or_
from sqlalchemy.sql import Select

from app.adapters.database.models import OrderORM, RecipientORM, UserORM
from app.core.entities import OrderStatusTypes


class OrderFilter(Filter):
    """Advanced order filter with search capabilities"""

    # ID Filters
    terminal_id: Optional[UUID] = None
    shift_id: Optional[UUID] = None
    courier_id: Optional[UUID] = None
    recipient_id: Optional[UUID] = None

    # Date Filters
    expected_delivery_date__gte: Optional[datetime] = None
    expected_delivery_date__lte: Optional[datetime] = None
    created_at__gte: Optional[datetime] = None
    created_at__lte: Optional[datetime] = None

    # Status Filter
    status: Optional[OrderStatusTypes] = None

    # Boolean Filters
    is_return: Optional[bool] = None

    # Search Filter
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = OrderORM
        search_field_name = "search"
        search_model_fields = [
            "name",
            "barcode",
        ]

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

        # Apply all standard filters (terminal_id, shift_id, status, dates, etc.)
        query = super().filter(query)

        # Restore search value
        self.search = search_value

        # Apply custom cross-model search if provided
        if search_value:
            term = f"%{search_value}%"
            query = query.outerjoin(RecipientORM).where(
                or_(
                    OrderORM.name.ilike(term),
                    OrderORM.barcode.ilike(term),
                    UserORM.first_name.ilike(term),
                    UserORM.last_name.ilike(term),
                    UserORM.phone_number.ilike(term),
                    UserORM.email.ilike(term),
                )
            )

        return query

    class Config:
        """Pydantic config"""

        from_attributes = True
