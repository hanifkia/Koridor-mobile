"""Hub ORM models."""

from uuid import UUID
import uuid

from sqlalchemy import (
    String,
    ForeignKey,
    Time,
    Interval,
    Float,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.database.models.base import Base, TimeStampMixin


class HubORM(Base, TimeStampMixin):
    """Hub (distribution center) ORM model"""

    __tablename__ = "hubs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    courier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("couriers.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    lon: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    setup_time: Mapped[Interval] = mapped_column(Interval, nullable=False)
    service_time: Mapped[Interval] = mapped_column(Interval, nullable=False)
    return_to_hub: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ✅ String references
    courier: Mapped["CourierORM"] = relationship("CourierORM", back_populates="hubs")
    shifts: Mapped[list["HubShiftORM"]] = relationship(
        "HubShiftORM", back_populates="hub", cascade="all, delete-orphan"
    )
    orders: Mapped[list["OrderORM"]] = relationship("OrderORM", back_populates="hub")
    routes: Mapped[list["RouteORM"]] = relationship(
        "RouteORM", back_populates="hub", lazy="selectin"
    )
    missions: Mapped[list["MissionORM"]] = relationship(
        "MissionORM",
        back_populates="hub",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_hub_courier_id", "courier_id"),
        Index("idx_hub_location", "lat", "lon"),
    )

    def __repr__(self) -> str:
        return f"<HubORM(name={self.name}, lat={self.lat}, lon={self.lon})>"


class HubShiftORM(Base, TimeStampMixin):
    """Hub shift ORM model"""

    __tablename__ = "hub_shifts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    terminal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("hubs.id", ondelete="CASCADE"),
        nullable=True,  # TODO: make it non-nullable after data migration
    )
    start_time: Mapped[Time] = mapped_column(Time, nullable=False)
    finish_time: Mapped[Time] = mapped_column(Time, nullable=False)

    # ✅ String references
    hub: Mapped["HubORM"] = relationship("HubORM", back_populates="shifts")
    orders: Mapped[list["OrderORM"]] = relationship(
        "OrderORM",
        back_populates="shift",
    )
    routes: Mapped[list["RouteORM"]] = relationship(
        "RouteORM",
        back_populates="shift",
        lazy="selectin",
    )
    missions: Mapped[list["MissionORM"]] = relationship(
        "MissionORM",
        back_populates="shift",
        lazy="selectin",
    )

    __table_args__ = (Index("idx_hub_shift_terminal_id", "terminal_id"),)

    def __repr__(self) -> str:
        return f"<HubShiftORM(terminal_id={self.terminal_id}, start_time={self.start_time}, finish_time={self.finish_time})>"
