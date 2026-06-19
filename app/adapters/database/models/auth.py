"""Authentication and authorization ORM models."""

from datetime import datetime, timezone
from uuid import uuid4, UUID
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum,
    Integer,
    Boolean,
    Index,
    UniqueConstraint,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.entities import UserStatus, RoleType
from app.adapters.database.models.base import Base, TimeStampMixin


class PermissionORM(Base, TimeStampMixin):
    """ORM model for permissions"""

    __tablename__ = "permissions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    table_name = Column(String(100), nullable=False, unique=True, index=True)
    actions = Column(ARRAY(String), nullable=False, default=[])

    # ✅ Use string references - NO IMPORTS!
    role_permissions = relationship(
        "PermissionRoleORM", back_populates="permission", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_permission_table_name", "table_name"),
        Index("uq_permission_table_name", "table_name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<PermissionORM(table_name={self.table_name})>"


class RoleORM(Base, TimeStampMixin):
    """Role ORM model for RBAC"""

    __tablename__ = "roles"

    id: Column = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    name: Column = Column(Enum(RoleType), unique=True, nullable=False, index=True)
    description: Column = Column(String(500), nullable=True)

    # Relationships - All use string references
    role_permissions = relationship(
        "PermissionRoleORM", back_populates="role", cascade="all, delete-orphan"
    )
    users = relationship("UserORM", back_populates="role")
    permissions = relationship(
        "PermissionORM",
        secondary="role_permissions",
        primaryjoin="RoleORM.id == PermissionRoleORM.role_id",
        secondaryjoin="PermissionORM.id == PermissionRoleORM.permission_id",
        viewonly=True,
    )

    __table_args__ = (UniqueConstraint("name", name="uq_role_name"),)

    def __repr__(self) -> str:
        return f"<RoleORM(name={self.name.value})>"


class PermissionRoleORM(Base, TimeStampMixin):
    """Association table for Role <-> Permission M2M"""

    __tablename__ = "role_permissions"

    id: Column = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    role_id: Column = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Column = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # String references
    role = relationship("RoleORM", back_populates="role_permissions")
    permission = relationship("PermissionORM", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_role_permission_role_id", "role_id"),
        Index("idx_role_permission_permission_id", "permission_id"),
    )

    def __repr__(self) -> str:
        return f"<PermissionRoleORM(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserORM(Base, TimeStampMixin):
    """ORM model for User"""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.INACTIVE, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_terminal_setup_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_courier_profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ✅ String references - No circular imports!
    role: Mapped["RoleORM | None"] = relationship(
        "RoleORM",
        back_populates="users",
        foreign_keys=[role_id],
    )
    avatar: Mapped["UserAvatarORM | None"] = relationship(
        "UserAvatarORM",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    password_reset_codes: Mapped[list["PasswordResetCodeORM"]] = relationship(
        "PasswordResetCodeORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshTokenORM"]] = relationship(
        "RefreshTokenORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    courier: Mapped["CourierORM | None"] = relationship(
        "CourierORM",
        back_populates="user",
        uselist=False,
    )
    recipient: Mapped["RecipientORM | None"] = relationship(
        "RecipientORM",
        back_populates="user",
        uselist=False,
    )
    verification_tokens: Mapped[list["UserVerificationTokenORM"]] = relationship(
        "UserVerificationTokenORM",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_username", "username"),
        Index("ix_users_email", "email"),
        Index("ix_users_status", "status"),
        Index("ix_users_last_login", "last_login_at"),
    )

    def __repr__(self) -> str:
        return f"<UserORM(id={self.id}, username={self.username}, email={self.email})>"


class UserVerificationTokenORM(Base, TimeStampMixin):
    """ORM model for user email verification tokens"""

    __tablename__ = "user_verification_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["UserORM"] = relationship(
        "UserORM", back_populates="verification_tokens"
    )

    __table_args__ = (
        Index("idx_user_verification_token_user_id", "user_id"),
        Index("idx_user_verification_token_token", "token"),
        Index("idx_user_verification_token_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<UserVerificationTokenORM(user_id={self.user_id}, token={self.token[:20]}...)>"


class UserAvatarORM(Base, TimeStampMixin):
    """User avatar ORM model"""

    __tablename__ = "user_avatars"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="avatar")

    __table_args__ = (Index("idx_user_avatar_user_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<UserAvatarORM(user_id={self.user_id}, file_name={self.file_name})>"


class RefreshTokenORM(Base, TimeStampMixin):
    """Refresh token ORM model for JWT token management"""

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["UserORM"] = relationship("UserORM", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_token_user_id", "user_id"),
        Index("idx_refresh_token_token", "token"),
        Index("idx_refresh_token_expires_at", "expires_at"),
    )

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_revoked and not self.is_expired()

    def revoke(self) -> None:
        """Revoke the refresh token"""
        self.is_revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<RefreshTokenORM(user_id={self.user_id}, is_valid={self.is_valid()})>"


class PasswordResetCodeORM(Base, TimeStampMixin):
    """ORM model for password reset codes"""

    __tablename__ = "password_reset_codes"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(255), unique=True, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("UserORM", back_populates="password_reset_codes")

    def __repr__(self) -> str:
        return (
            f"<PasswordResetCodeORM(code={self.code[:20]}..., user_id={self.user_id})>"
        )
