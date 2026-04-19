"""
PM Digital Employee - Weekly Report Model
项目经理数字员工系统 - 周报实体模型

v1.2.0新增：支持多源数据录入（飞书卡片、Excel导入、飞书在线表格同步）
"""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, ProjectScopedMixin
from app.domain.enums import DataSource, WeeklyReportStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class WeeklyReport(Base, ProjectScopedMixin):
    """
    项目周报实体.
    
    存储项目周报信息，支持三种数据录入方式的数据同步。

    Attributes:
        id: 周报唯一标识
        project_id: 所属项目ID
        report_code: 周报编码
        report_date: 周报日期
        week_start: 周开始日期
        week_end: 周结束日期
        summary: 本周工作总结
        completed_tasks: 已完成任务（JSON数组）
        in_progress_tasks: 进行中任务（JSON数组）
        next_week_plan: 下周计划
        risks_and_issues: 风险和问题
        status: 周报状态
        approval_status: 审批状态
        author_id: 作者飞书用户ID
        author_name: 作者姓名
        approver_id: 审批人飞书用户ID
        approver_name: 审批人姓名
        approved_at: 审批时间
        data_source: 数据来源（lark_card/excel_import/lark_sheet_sync）
        version: 版本号
        is_current: 是否当前版本
        external_id: 外部系统ID（飞书表格行ID等）
        sync_version: 同步版本号
        last_sync_at: 最后同步时间
    """

    __tablename__ = "weekly_reports"
    __table_args__ = (
        Index("ix_weekly_reports_project_id", "project_id"),
        Index("ix_weekly_reports_report_date", "report_date"),
        Index("ix_weekly_reports_week_start", "week_start"),
        Index("ix_weekly_reports_status", "status"),
        Index("ix_weekly_reports_data_source", "data_source"),
        Index("ix_weekly_reports_is_current", "is_current"),
        {"comment": "项目周报表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="周报ID",
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
    report_code: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="周报编码",
    )

    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="周报日期",
    )

    week_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="周开始日期",
    )

    week_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="周结束日期",
    )

    # 内容
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="本周工作总结",
    )

    completed_tasks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="已完成任务（JSON数组）",
    )

    in_progress_tasks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="进行中任务（JSON数组）",
    )

    next_week_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="下周计划",
    )

    risks_and_issues: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="风险和问题",
    )

    # 状态
    status: Mapped[WeeklyReportStatus] = mapped_column(
        String(32),
        nullable=False,
        default=WeeklyReportStatus.DRAFT,
        comment="周报状态",
    )

    approval_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        default="pending",
        comment="审批状态",
    )

    # 作者信息
    author_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="作者飞书用户ID",
    )

    author_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="作者姓名",
    )

    # 审批信息
    approver_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="审批人飞书用户ID",
    )

    approver_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="审批人姓名",
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="审批时间",
    )

    # 数据来源（多源数据录入支持）
    data_source: Mapped[DataSource] = mapped_column(
        String(32),
        nullable=False,
        default=DataSource.LARK_CARD,
        comment="数据来源",
    )

    # 版本控制
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="版本号",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否当前版本",
    )

    # 同步信息
    external_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="外部系统ID（飞书表格行ID等）",
    )

    sync_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="同步版本号",
    )

    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后同步时间",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="weekly_reports",
    )

    def __repr__(self) -> str:
        return f"<WeeklyReport(id={self.id}, week_start={self.week_start}, status={self.status})>"