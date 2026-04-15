"""
PM Digital Employee - User Model
PM Digital Employee System - User entity model

Lark as the primary user interaction entrypoint.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import AuditMixin, Base

if TYPE_CHECKING:
    from app.domain.models.user_project_role import UserProjectRole


class User(Base, AuditMixin):
    """
    User entity.

    Stores Lark user info and system user data.

    Attributes:
        id: User unique identifier (UUID)
        lark_user_id: Lark user ID (unique)
        name: User name
        email: User email
        phone: User phone number
        avatar_url: Avatar URL
        department_id: Department ID
        department_name: Department name
        position: Position
        is_active: Is active
        is_admin: Is admin
        last_login_at: Last login time
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_lark_user_id", "lark_user_id", unique=True),
        Index("ix_users_department_id", "department_id"),
        Index("ix_users_is_active", "is_active"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="User ID",
    )

    # Lark user ID (core identifier)
    lark_user_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Lark user ID",
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="User name",
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="User email",
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="User phone",
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Avatar URL",
    )

    # Organization info
    department_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Department ID",
    )

    department_name: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="Department name",
    )

    position: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="Position",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is active",
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is admin",
    )

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login time",
    )

    # Relationships
    project_roles: Mapped[List["UserProjectRole"]] = relationship(
        "UserProjectRole",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, lark_user_id={self.lark_user_id})>"

    @property
    def display_name(self) -> str:
        """Get display name."""
        if self.name:
            return self.name
        return self.lark_user_id