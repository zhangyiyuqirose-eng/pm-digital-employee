"""
PM Digital Employee - User Project Role Model
项目经理数字员工系统 - 用户项目角色关联模型
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base
from app.domain.enums import UserRole

if TYPE_CHECKING:
    from app.domain.models.user import User
    from app.domain.models.project import Project


class UserProjectRole(Base):
    """
    用户项目角色关联实体.

    定义用户在特定项目中的角色和权限。

    Attributes:
        id: 关联记录ID
        user_id: 用户ID
        project_id: 项目ID
        role: 用户角色
        joined_at: 加入时间
    """

    __tablename__ = "user_project_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_user_project"),
        Index("ix_user_project_roles_user_id", "user_id"),
        Index("ix_user_project_roles_project_id", "project_id"),
        Index("ix_user_project_roles_role", "role"),
        {"comment": "用户项目角色关联表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="关联记录ID",
    )

    # 外键
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 角色
    role: Mapped[UserRole] = mapped_column(
        String(32),
        nullable=False,
        default=UserRole.MEMBER,
        comment="用户角色",
    )

    # 时间
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="加入时间",
    )

    # 关联关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_roles",
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="user_roles",
    )

    def __repr__(self) -> str:
        return f"<UserProjectRole(user_id={self.user_id}, project_id={self.project_id}, role={self.role})>"

    def has_permission(self, resource: str, action: str) -> bool:
        """
        检查角色是否有指定资源的操作权限.

        Args:
            resource: 资源类型
            action: 操作类型

        Returns:
            bool: 是否有权限
        """
        # 权限矩阵
        permission_matrix = {
            UserRole.PROJECT_MANAGER: {
                "project": ["read", "write", "submit", "approve", "execute", "manage"],
                "task": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
                "milestone": ["read", "write", "submit", "approve", "execute", "manage"],
                "cost": ["read", "write", "submit", "approve", "execute", "manage"],
                "risk": ["read", "write", "submit", "approve", "execute", "manage"],
                "document": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
                "report": ["read", "write", "submit", "execute", "manage"],
                "approval": ["read", "write", "submit", "approve", "execute"],
            },
            UserRole.PM: {
                "project": ["read", "write", "submit", "execute"],
                "task": ["read", "write", "submit", "execute"],
                "milestone": ["read", "write", "submit", "execute"],
                "cost": ["read", "write", "submit", "execute"],
                "risk": ["read", "write", "submit", "execute"],
                "document": ["read", "write", "submit", "execute"],
                "report": ["read", "write", "submit", "execute"],
                "approval": ["read", "submit"],
            },
            UserRole.TECH_LEAD: {
                "project": ["read", "write"],
                "task": ["read", "write", "submit", "execute"],
                "milestone": ["read", "write", "submit"],
                "cost": ["read"],
                "risk": ["read", "write", "submit", "execute"],
                "document": ["read", "write", "submit", "execute"],
                "report": ["read", "write", "submit"],
                "approval": ["read", "submit"],
            },
            UserRole.MEMBER: {
                "project": ["read"],
                "task": ["read", "submit"],
                "milestone": ["read"],
                "cost": [],
                "risk": ["read"],
                "document": ["read", "submit"],
                "report": ["read"],
                "approval": [],
            },
            UserRole.AUDITOR: {
                "project": ["read"],
                "task": ["read"],
                "milestone": ["read"],
                "cost": ["read"],
                "risk": ["read"],
                "document": ["read"],
                "report": ["read"],
                "approval": ["read"],
            },
        }

        role_permissions = permission_matrix.get(self.role, {})
        resource_actions = role_permissions.get(resource, [])
        return action in resource_actions