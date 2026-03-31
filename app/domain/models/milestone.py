"""
PM Digital Employee - Milestone Model
项目经理数字员工系统 - 里程碑实体模型
"""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import ProjectScopedMixin
from app.domain.enums import MilestoneStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class Milestone(ProjectScopedMixin):
    """
    里程碑实体.

    存储项目里程碑信息和达成状态。

    Attributes:
        id: 里程碑唯一标识
        project_id: 所属项目ID
        name: 里程碑名称
        description: 里程碑描述
        status: 里程碑状态
        due_date: 计划完成日期
        achieved_date: 实际达成日期
    """

    __tablename__ = "milestones"
    __table_args__ = (
        Index("ix_milestones_project_id", "project_id"),
        Index("ix_milestones_status", "status"),
        Index("ix_milestones_due_date", "due_date"),
        Index("ix_milestones_project_status", "project_id", "status"),
        {"comment": "里程碑表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="里程碑ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="里程碑名称",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="里程碑描述",
    )

    # 状态
    status: Mapped[MilestoneStatus] = mapped_column(
        String(32),
        nullable=False,
        default=MilestoneStatus.PLANNED,
        comment="里程碑状态",
    )

    # 时间信息
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="计划完成日期",
    )

    achieved_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="实际达成日期",
    )

    # 关键里程碑标记
    is_key_milestone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否关键里程碑",
    )

    # 排序
    sort_order: Mapped[int] = mapped_column(
        "sort_order",
        None,
        nullable=False,
        default=0,
        comment="排序序号",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="milestones",
    )

    def __repr__(self) -> str:
        return f"<Milestone(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_achieved(self) -> bool:
        """判断里程碑是否已达成."""
        return self.status == MilestoneStatus.ACHIEVED

    @property
    def is_delayed(self) -> bool:
        """判断里程碑是否延期."""
        if self.due_date and self.status not in [MilestoneStatus.ACHIEVED, MilestoneStatus.CANCELLED]:
            from datetime import date as date_type

            return date_type.today() > self.due_date
        return False