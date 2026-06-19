"""Mission ORM model."""

from datetime import datetime, time
from uuid import uuid4, UUID

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Time,
    Float,
    Integer,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.database.models.base import Base


class MissionORM(Base):
    """Mission ORM model - represents a single delivery mission within a route"""

    __tablename__ = "missions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    terminal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False
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

    is_return: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    arrival_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    cumulative_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cumulative_distance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_time: Mapped[int | None] = mapped_column(Integer, nullable=True)

    actual_arrival_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    actual_cumulative_duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    actual_cumulative_distance: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    actual_service_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_mission_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    actual_mission_finish_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    postponed: Mapped[str | None] = mapped_column(String(50), nullable=True)

    position_in_route: Mapped[int | None] = mapped_column(Integer, nullable=True)

    waiting_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_waiting_time: Mapped[int | None] = mapped_column(Integer, nullable=True)

    loading_scan_parcel_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    delivery_scan_parcel_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    delivery_scan_parcel_barcode: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    courier_comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ✅ String references
    route: Mapped["RouteORM"] = relationship(
        "RouteORM", back_populates="missions", foreign_keys=[route_id], lazy="select"
    )
    order: Mapped["OrderORM"] = relationship(
        "OrderORM", back_populates="mission", foreign_keys=[order_id], lazy="select"
    )
    hub: Mapped["HubORM"] = relationship(
        "HubORM", back_populates="missions", foreign_keys=[terminal_id], lazy="select"
    )
    shift: Mapped["HubShiftORM"] = relationship(
        "HubShiftORM",
        back_populates="missions",
        foreign_keys=[shift_id],
        lazy="select",
    )
    courier: Mapped["CourierORM"] = relationship(
        "CourierORM",
        back_populates="missions",
        foreign_keys=[courier_id],
        lazy="select",
    )

    __table_args__ = (
        Index("idx_mission_route_id", "route_id"),
        Index("idx_mission_order_id", "order_id"),
        Index("idx_mission_courier_id", "courier_id"),
        Index("idx_mission_status", "status"),
        Index("idx_mission_position", "route_id", "position_in_route"),
    )

    def __repr__(self) -> str:
        return f"<MissionORM(id={self.id}, order_id={self.order_id}, status={self.status})>"
