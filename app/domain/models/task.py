"""
PM Digital Employee - Task Model
项目经理数字员工系统 - 任务实体模型

v1.2.0新增：任务依赖关系、工期预估、标签功能
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, ProjectScopedMixin
from app.domain.enums import TaskPriority, TaskStatus, DependencyType

if TYPE_CHECKING:
    from app.domain.models.project import Project


class Task(Base, ProjectScopedMixin):
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

    # ============================================
    # v1.2.0新增：任务依赖关系
    # ============================================

    # 前置任务ID（单个前置任务）
    predecessor_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="前置任务ID",
    )

    # 后置任务列表（JSON存储，多个后置任务）
    successor_task_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="后置任务ID列表(JSON数组)",
    )

    # 依赖类型（FS/SS/FF/SF）
    dependency_type: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        default="FS",
        comment="依赖类型(FS=完成-开始,SS=开始-开始,FF=完成-完成,SF=开始-完成)",
    )

    # 预计工期（天数）
    estimated_duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="预计工期(天数)",
    )

    # 任务标签（JSON存储，多个标签）
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="任务标签(JSON数组)",
    )

    # 数据来源（v1.2.0新增）
    data_source: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="数据来源(lark_card/excel_import/lark_sheet_sync)",
    )

    # 飞书表格行号（用于同步）
    lark_sheet_row: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="飞书表格行号",
    )

    # 最后同步时间
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后同步时间",
    )

    # 同步版本号
    sync_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="同步版本号",
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

    # ============================================
    # v1.2.0新增：依赖关系和标签辅助方法
    # ============================================

    @property
    def successor_ids_list(self) -> List[str]:
        """解析后置任务ID列表."""
        import json
        if self.successor_task_ids:
            try:
                return json.loads(self.successor_task_ids)
            except json.JSONDecodeError:
                return []
        return []

    def set_successor_ids(self, ids: List[str]) -> None:
        """设置后置任务ID列表."""
        import json
        self.successor_task_ids = json.dumps(ids) if ids else None

    @property
    def tags_list(self) -> List[str]:
        """解析任务标签列表."""
        import json
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []

    def set_tags(self, tags: List[str]) -> None:
        """设置任务标签列表."""
        import json
        self.tags = json.dumps(tags) if tags else None

    def add_tag(self, tag: str) -> None:
        """添加单个标签."""
        current_tags = self.tags_list
        if tag and tag not in current_tags:
            current_tags.append(tag)
            self.set_tags(current_tags)

    def remove_tag(self, tag: str) -> None:
        """移除单个标签."""
        current_tags = self.tags_list
        if tag in current_tags:
            current_tags.remove(tag)
            self.set_tags(current_tags)

    def has_tag(self, tag: str) -> bool:
        """检查是否包含指定标签."""
        return tag in self.tags_list

    def calculate_progress_percentage(self) -> int:
        """计算进度百分比.
        
        根据实际工时与预估工时计算进度，或者直接返回progress字段。
        
        Returns:
            int: 进度百分比（0-100）
        """
        # 如果有工时数据，使用工时计算
        if self.estimated_hours and self.estimated_hours > 0 and self.actual_hours:
            return min(100, int(float(self.actual_hours) / float(self.estimated_hours) * 100))
        
        # 否则返回progress字段
        return self.progress

    def get_delay_days(self) -> int:
        """获取延期天数.
        
        Returns:
            int: 延期天数，未延期返回0
        """
        if self.is_delayed and self.end_date:
            from datetime import date as date_type
            return (date_type.today() - self.end_date).days
        return 0