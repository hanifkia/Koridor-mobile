"""Vehicle ORM model."""

from decimal import Decimal
from uuid import uuid4, UUID
import uuid

from sqlalchemy import (
    ForeignKey,
    Enum,
    Interval,
    Float,
    Integer,
    DECIMAL,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import VehicleType, FuelType
from app.adapters.database.models.base import Base, TimeStampMixin


class VehicleORM(Base, TimeStampMixin):
    """Vehicle ORM model"""

    __tablename__ = "vehicles"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    courier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("couriers.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, native_enum=False), nullable=False
    )
    weight_capacity: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    volume_capacity: Mapped[float] = mapped_column(Float, default=0.0, nullable=True)
    loading_cost: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    travel_cost_per_km: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    travel_cost_per_hour: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00"), nullable=False
    )
    loading_time: Mapped[Interval] = mapped_column(Interval, nullable=False)
    average_speed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_duration: Mapped[Interval | None] = mapped_column(Interval, nullable=True)
    max_distance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_consumption_per_100_km: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType), default=FuelType.PETROL, nullable=False
    )
    max_tasks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ✅ String references
    courier: Mapped["CourierORM"] = relationship(
        "CourierORM", back_populates="vehicles"
    )
    routes: Mapped[list["RouteORM"]] = relationship(
        "RouteORM",
        back_populates="vehicle",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_vehicle_courier_id", "courier_id"),
        Index("idx_vehicle_type", "vehicle_type"),
    )

    def __repr__(self) -> str:
        return f"<VehicleORM(courier_id={self.courier_id}, vehicle_type={self.vehicle_type.value})>"
