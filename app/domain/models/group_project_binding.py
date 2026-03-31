"""
PM Digital Employee - Group Project Binding Model
项目经理数字员工系统 - 飞书群项目绑定模型
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base

if TYPE_CHECKING:
    from app.domain.models.project import Project


class GroupProjectBinding(Base):
    """
    飞书群项目绑定实体.

    定义飞书群与项目的绑定关系，用于群内消息的项目隔离。

    Attributes:
        id: 绑定记录ID
        chat_id: 飞书群ID
        project_id: 绑定的项目ID
        bound_at: 绑定时间
        bound_by: 绑定操作人ID
        is_active: 绑定是否有效
    """

    __tablename__ = "group_project_bindings"
    __table_args__ = (
        UniqueConstraint("chat_id", name="uq_group_chat_id"),
        Index("ix_group_project_bindings_chat_id", "chat_id"),
        Index("ix_group_project_bindings_project_id", "project_id"),
        Index("ix_group_project_bindings_is_active", "is_active"),
        {"comment": "飞书群项目绑定表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="绑定记录ID",
    )

    # 飞书群ID
    chat_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="飞书群ID",
    )

    chat_name: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="飞书群名称",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="绑定的项目ID",
    )

    # 绑定信息
    bound_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="绑定时间",
    )

    bound_by: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="绑定操作人飞书用户ID",
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="绑定是否有效",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="group_bindings",
    )

    def __repr__(self) -> str:
        return f"<GroupProjectBinding(chat_id={self.chat_id}, project_id={self.project_id})>"