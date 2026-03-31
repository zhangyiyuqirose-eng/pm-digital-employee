"""
PM Digital Employee - User Model
项目经理数字员工系统 - 用户实体模型
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
    用户实体.

    存储飞书用户信息和系统用户数据。

    Attributes:
        id: 用户唯一标识（UUID）
        feishu_user_id: 飞书用户ID（唯一）
        name: 用户姓名
        email: 用户邮箱
        phone: 用户手机号
        avatar_url: 头像URL
        department_id: 所属部门ID
        department_name: 所属部门名称
        position: 职位
        is_active: 是否激活
        is_admin: 是否管理员
        last_login_at: 最后登录时间
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_feishu_user_id", "feishu_user_id", unique=True),
        Index("ix_users_department_id", "department_id"),
        Index("ix_users_is_active", "is_active"),
        {"comment": "用户表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="用户ID",
    )

    # 飞书用户ID（核心标识）
    feishu_user_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="飞书用户ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="用户姓名",
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="用户邮箱",
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="用户手机号",
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="头像URL",
    )

    # 组织信息
    department_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="所属部门ID",
    )

    department_name: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="所属部门名称",
    )

    position: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="职位",
    )

    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否激活",
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否管理员",
    )

    # 时间戳
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )

    # 关联关系
    project_roles: Mapped[List["UserProjectRole"]] = relationship(
        "UserProjectRole",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, feishu_user_id={self.feishu_user_id})>"

    @property
    def display_name(self) -> str:
        """获取显示名称."""
        if self.name:
            return self.name
        return self.feishu_user_id