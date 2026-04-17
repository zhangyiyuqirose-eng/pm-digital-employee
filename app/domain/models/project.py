"""
PM Digital Employee - Project Model
项目经理数字员工系统 - 项目实体模型
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import AuditMixin, Base
from app.domain.enums import ProjectStatus

if TYPE_CHECKING:
    from app.domain.models.task import Task
    from app.domain.models.milestone import Milestone
    from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
    from app.domain.models.risk import ProjectRisk
    from app.domain.models.document import ProjectDocument
    from app.domain.models.user_project_role import UserProjectRole
    from app.domain.models.group_project_binding import GroupProjectBinding


class Project(Base, AuditMixin):
    """
    项目实体.

    存储项目基本信息和状态。

    Attributes:
        id: 项目唯一标识（UUID）
        name: 项目名称
        code: 项目编码
        description: 项目描述
        status: 项目状态
        project_type: 项目类型
        priority: 项目优先级
        start_date: 计划开始日期
        end_date: 计划结束日期
        actual_start_date: 实际开始日期
        actual_end_date: 实际结束日期
        total_budget: 总预算
        pm_id: 项目经理ID
        department_id: 所属部门ID
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_status", "status"),
        Index("ix_projects_pm_id", "pm_id"),
        Index("ix_projects_department_id", "department_id"),
        Index("ix_projects_start_date", "start_date"),
        Index("ix_projects_code", "code", unique=True),
        {"comment": "项目主表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="项目ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="项目名称",
    )

    code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="项目编码",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="项目描述",
    )

    # 状态信息
    status: Mapped[ProjectStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ProjectStatus.DRAFT,
        comment="项目状态",
    )

    project_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="项目类型",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        default=2,
        comment="项目优先级",
    )

    # 时间信息
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="计划开始日期",
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="计划结束日期",
    )

    actual_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="实际开始日期",
    )

    actual_end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="实际结束日期",
    )

    # 预算信息
    total_budget: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        default=Decimal("0.00"),
        comment="总预算（元）",
    )

    # 人员信息
    pm_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="项目经理ID",
    )

    pm_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="项目经理姓名",
    )

    # 部门信息
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

    # 状态标记
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否活跃",
    )

    # 关联关系
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="project",
        lazy="selectin",
    )

    milestones: Mapped[List["Milestone"]] = relationship(
        "Milestone",
        back_populates="project",
        lazy="selectin",
    )

    cost_budgets: Mapped[List["ProjectCostBudget"]] = relationship(
        "ProjectCostBudget",
        back_populates="project",
        lazy="selectin",
    )

    cost_actuals: Mapped[List["ProjectCostActual"]] = relationship(
        "ProjectCostActual",
        back_populates="project",
        lazy="selectin",
    )

    risks: Mapped[List["ProjectRisk"]] = relationship(
        "ProjectRisk",
        back_populates="project",
        lazy="selectin",
    )

    documents: Mapped[List["ProjectDocument"]] = relationship(
        "ProjectDocument",
        back_populates="project",
        lazy="selectin",
    )

    user_roles: Mapped[List["UserProjectRole"]] = relationship(
        "UserProjectRole",
        back_populates="project",
        lazy="selectin",
    )

    group_bindings: Mapped[List["GroupProjectBinding"]] = relationship(
        "GroupProjectBinding",
        back_populates="project",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_delayed(self) -> bool:
        """判断项目是否延期."""
        if self.end_date and self.status in [
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.PRE_INITIATION,
            ProjectStatus.INITIATED,
        ]:
            from datetime import date as date_type

            return date_type.today() > self.end_date
        return False