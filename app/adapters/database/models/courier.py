"""Courier ORM models."""

from datetime import datetime
from uuid import uuid4, UUID
import uuid

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import VehicleType, CourierStatesType
from app.adapters.database.models.base import Base, TimeStampMixin


class CourierORM(Base, TimeStampMixin):
    """Courier ORM model"""

    __tablename__ = "couriers"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, native_enum=False), nullable=False
    )
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ✅ String references - NO IMPORTS!
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="courier")
    hubs: Mapped[list["HubORM"]] = relationship("HubORM", back_populates="courier")
    vehicles: Mapped[list["VehicleORM"]] = relationship(
        "VehicleORM", back_populates="courier"
    )
    orders: Mapped[list["OrderORM"]] = relationship(
        "OrderORM", back_populates="courier"
    )
    routes: Mapped[list["RouteORM"]] = relationship(
        "RouteORM",
        back_populates="courier",
        lazy="selectin",
    )
    missions: Mapped[list["MissionORM"]] = relationship(
        "MissionORM",
        back_populates="courier",
        lazy="selectin",
    )
    current_state: Mapped["CourierCurrentStateORM | None"] = relationship(
        "CourierCurrentStateORM",
        back_populates="courier",
        foreign_keys="CourierCurrentStateORM.courier_id",
        lazy="select",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (Index("idx_courier_user_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<CourierORM(user_id={self.user_id}, vehicle_type={self.vehicle_type.value})>"


class CourierCurrentStateORM(Base):
    """ORM model for tracking courier's current state and delivered orders"""

    __tablename__ = "courier_current_states"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    courier_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("couriers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    delivered_order_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)),
        nullable=True,
        default=list,
    )
    state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=CourierStatesType.IDLE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    courier: Mapped["CourierORM"] = relationship(
        "CourierORM",
        back_populates="current_state",
        foreign_keys=[courier_id],
        lazy="select",
    )

    __table_args__ = (
        Index("idx_courier_current_state_courier_id", "courier_id"),
        Index("idx_courier_current_state_state", "state"),
        Index("idx_courier_current_state_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CourierCurrentStateORM(courier_id={self.courier_id}, "
            f"state={self.state}, delivered_orders={len(self.delivered_order_ids)})>"
        )
