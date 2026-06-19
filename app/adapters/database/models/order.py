"""Order and Recipient ORM models."""

from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Time,
    Float,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import OrderStatusTypes
from app.adapters.database.models.base import Base, TimeStampMixin


class OrderORM(Base, TimeStampMixin):
    """Order ORM model"""

    __tablename__ = "orders"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    terminal_id = Column(PG_UUID(as_uuid=True), ForeignKey("hubs.id"), nullable=False)
    shift_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("hub_shifts.id"), nullable=False
    )
    courier_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("couriers.id"), nullable=False
    )
    recipient_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("recipients.id"), nullable=False
    )

    name = Column(String(255), nullable=False)
    barcode = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(
        Enum(OrderStatusTypes),
        default=OrderStatusTypes.REGISTERED,
        nullable=False,
        index=True,
    )
    geo_location_provided = Column(Boolean, default=False, nullable=True)

    time_window_earliest: Mapped[Time | None] = mapped_column(Time, nullable=True)
    time_window_latest: Mapped[Time | None] = mapped_column(Time, nullable=True)

    weight_occupation = Column(Float, default=0.0, nullable=False)
    volume_occupation = Column(Float, default=0.0, nullable=False)

    is_return = Column(Boolean, default=False, nullable=False)
    original_delivery_date = Column(DateTime, nullable=True)
    expected_delivery_date = Column(DateTime, nullable=True)
    actual_delivery_date = Column(DateTime, nullable=True)

    moved_as = Column(PG_UUID(as_uuid=True), nullable=True)

    # ✅ String references
    hub: Mapped["HubORM"] = relationship("HubORM", back_populates="orders")
    shift: Mapped["HubShiftORM"] = relationship("HubShiftORM", back_populates="orders")
    courier: Mapped["CourierORM"] = relationship("CourierORM", back_populates="orders")
    recipient: Mapped["RecipientORM"] = relationship(
        "RecipientORM",
        back_populates="orders",
        foreign_keys=[recipient_id],
        lazy="select",
    )
    mission: Mapped["MissionORM | None"] = relationship(
        "MissionORM",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="MissionORM.order_id",
    )

    __table_args__ = (
        Index("idx_order_barcode", "barcode"),
        Index("idx_order_status", "status"),
        Index("idx_order_courier_id", "courier_id"),
        Index("idx_order_recipient_id", "recipient_id"),
        Index("idx_order_terminal_id", "terminal_id"),
        Index("idx_order_shift_id", "shift_id"),
        Index("idx_order_courier_status", "courier_id", "status"),
        Index("idx_order_recipient_status", "recipient_id", "status"),
        Index("idx_order_hub_status", "terminal_id", "status"),
        Index("idx_order_shift_status", "shift_id", "status"),
        Index("idx_order_time_window", "time_window_earliest", "time_window_latest"),
        Index("idx_order_expected_delivery", "expected_delivery_date"),
        Index("idx_order_is_return", "is_return"),
    )

    def __repr__(self):
        return f"<OrderORM(id={self.id}, barcode={self.barcode}, status={self.status.value})>"


class RecipientORM(Base):
    """Recipient ORM model"""

    __tablename__ = "recipients"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ String references
    user: Mapped["UserORM"] = relationship(
        "UserORM", back_populates="recipient", foreign_keys=[user_id], lazy="select"
    )
    orders: Mapped[list["OrderORM"]] = relationship(
        "OrderORM",
        back_populates="recipient",
        lazy="selectin",
    )

    __table_args__ = (Index("idx_recipient_location", "latitude", "longitude"),)

    def __repr__(self):
        return f"<RecipientORM(id={self.id}, city={self.city}, country={self.country})>"
