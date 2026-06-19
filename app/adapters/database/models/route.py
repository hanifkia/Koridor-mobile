"""Route ORM model."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Time,
    Integer,
    Boolean,
    DECIMAL,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import RouteStatesType
from app.adapters.database.models.base import Base, TimeStampMixin


class RouteORM(Base, TimeStampMixin):
    """Route ORM model - represents a delivery route for a courier on a specific shift"""

    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    terminal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("hubs.id", ondelete="CASCADE"),
        nullable=False,
    )
    shift_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("hub_shifts.id", ondelete="CASCADE"),
        nullable=False,
    )
    courier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("couriers.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )

    route_name: Mapped[str] = mapped_column(String(255), nullable=False)

    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    finish_time: Mapped[Time] = mapped_column(Time, nullable=False)

    actual_start_time: Mapped[Time | None] = mapped_column(Time, nullable=True)
    actual_finish_time: Mapped[Time | None] = mapped_column(Time, nullable=True)

    cost: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), default=None, nullable=True
    )
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), default=RouteStatesType.SCHEDULED.value, nullable=False
    )
    color: Mapped[str] = mapped_column(String(10), nullable=False)

    current_mission_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    must_return: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    number_of_missions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_waiting_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_actual_waiting_time: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    total_number_of_orders: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_number_of_stops: Mapped[int | None] = mapped_column(Integer, nullable=True)

    loading_time_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    arrived_at_hub_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    lock: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    created_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    modification_time: Mapped[Time | None] = mapped_column(Time, nullable=True)
    courier_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ✅ String references
    hub: Mapped["HubORM"] = relationship(
        "HubORM",
        back_populates="routes",
        foreign_keys=[terminal_id],
        lazy="select",
    )
    shift: Mapped["HubShiftORM"] = relationship(
        "HubShiftORM",
        back_populates="routes",
        foreign_keys=[shift_id],
        lazy="select",
    )
    courier: Mapped["CourierORM"] = relationship(
        "CourierORM",
        back_populates="routes",
        foreign_keys=[courier_id],
        lazy="select",
    )
    vehicle: Mapped["VehicleORM"] = relationship(
        "VehicleORM",
        back_populates="routes",
        foreign_keys=[vehicle_id],
        lazy="select",
    )
    missions: Mapped[list["MissionORM"]] = relationship(
        "MissionORM",
        back_populates="route",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="MissionORM.route_id",
    )

    __table_args__ = (
        Index("idx_route_courier_id", "courier_id"),
        Index("idx_route_terminal_id", "terminal_id"),
        Index("idx_route_shift_id", "shift_id"),
        Index("idx_route_vehicle_id", "vehicle_id"),
        Index("idx_route_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<RouteORM(id={self.id}, name={self.route_name}, status={self.status})>"
