"""
PM Digital Employee - Task Model
项目经理数字员工系统 - 任务实体模型
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import ProjectScopedMixin
from app.domain.enums import TaskPriority, TaskStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class Task(ProjectScopedMixin):
    """
    任务实体.

    存储项目任务信息和进度数据。

    Attributes:
        id: 任务唯一标识
        project_id: 所属项目ID
        name: 任务名称
        description: 任务描述
        status: 任务状态
        priority: 任务优先级
        progress: 完成进度（0-100）
        start_date: 计划开始日期
        end_date: 计划结束日期
        actual_start_date: 实际开始日期
        actual_end_date: 实际结束日期
        estimated_hours: 预估工时
        actual_hours: 实际工时
        assignee_id: 负责人ID
        parent_task_id: 父任务ID
    """

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_id", "project_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_assignee_id", "assignee_id"),
        Index("ix_tasks_end_date", "end_date"),
        Index("ix_tasks_parent_task_id", "parent_task_id"),
        Index("ix_tasks_project_status", "project_id", "status"),
        {"comment": "任务表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="任务ID",
    )

    # 项目ID（继承自ProjectScopedMixin，但需要显式定义外键）
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 基本信息
    code: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="任务编码",
    )

    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="任务名称",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="任务描述",
    )

    # 状态信息
    status: Mapped[TaskStatus] = mapped_column(
        String(32),
        nullable=False,
        default=TaskStatus.PENDING,
        comment="任务状态",
    )

    priority: Mapped[TaskPriority] = mapped_column(
        String(32),
        nullable=False,
        default=TaskPriority.MEDIUM,
        comment="任务优先级",
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="完成进度（0-100）",
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

    # 工时信息
    estimated_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="预估工时（小时）",
    )

    actual_hours: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="实际工时（小时）",
    )

    # 人员信息
    assignee_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="负责人飞书用户ID",
    )

    assignee_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="负责人姓名",
    )

    # 层级关系
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="父任务ID",
    )

    # 交付物
    deliverable: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="交付物描述",
    )

    # WBS信息
    wbs_code: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="WBS编码",
    )

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="WBS层级",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="tasks",
    )

    sub_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        backref="parent_task",
        remote_side=[id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, status={self.status}, progress={self.progress})>"

    @property
    def is_completed(self) -> bool:
        """判断任务是否完成."""
        return self.status == TaskStatus.COMPLETED or self.progress == 100

    @property
    def is_delayed(self) -> bool:
        """判断任务是否延期."""
        if self.end_date and self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            from datetime import date as date_type

            return date_type.today() > self.end_date and self.progress < 100
        return False