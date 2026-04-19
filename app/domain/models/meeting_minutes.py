"""
PM Digital Employee - Meeting Minutes Model
项目经理数字员工系统 - 会议纪要实体模型

v1.2.0新增：支持多源数据录入（飞书卡片、Excel导入、飞书在线表格同步）
"""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, ProjectScopedMixin
from app.domain.enums import DataSource, MeetingStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class MeetingMinutes(Base, ProjectScopedMixin):
    """
    会议纪要实体.
    
    存储会议纪要信息，支持三种数据录入方式的数据同步。
    自动提取行动项同步至任务管理模块。

    Attributes:
        id: 会议纪要唯一标识
        project_id: 所属项目ID
        meeting_code: 会议编码
        meeting_title: 会议标题
        meeting_date: 会议日期
        meeting_time: 会议时间
        meeting_location: 会议地点
        meeting_type: 会议类型
        agenda: 会议议题
        attendees: 参会人员（JSON数组）
        content: 会议内容
        decisions: 决议事项（JSON数组）
        action_items: 待办事项（JSON数组，自动同步到任务）
        status: 会议纪要状态
        recorder_id: 记录人飞书用户ID
        recorder_name: 记录人姓名
        data_source: 数据来源
        version: 版本号
        is_current: 是否当前版本
        external_id: 外部系统ID
        sync_version: 同步版本号
        last_sync_at: 最后同步时间
    """

    __tablename__ = "meeting_minutes"
    __table_args__ = (
        Index("ix_meeting_minutes_project_id", "project_id"),
        Index("ix_meeting_minutes_meeting_date", "meeting_date"),
        Index("ix_meeting_minutes_status", "status"),
        Index("ix_meeting_minutes_data_source", "data_source"),
        Index("ix_meeting_minutes_is_current", "is_current"),
        {"comment": "会议纪要表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="会议纪要ID",
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
    meeting_code: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="会议编码",
    )

    meeting_title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="会议标题",
    )

    meeting_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="会议日期",
    )

    meeting_time: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="会议时间 HH:MM-HH:MM",
    )

    meeting_location: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="会议地点",
    )

    meeting_type: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="会议类型（常规/临时/评审）",
    )

    # 内容
    agenda: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="会议议题",
    )

    attendees: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="参会人员（JSON数组）",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="会议内容",
    )

    decisions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="决议事项（JSON数组）",
    )

    action_items: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="待办事项（JSON数组，自动同步到任务）",
    )

    # 状态
    status: Mapped[MeetingStatus] = mapped_column(
        String(32),
        nullable=False,
        default=MeetingStatus.DRAFT,
        comment="会议纪要状态",
    )

    # 记录人信息
    recorder_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="记录人飞书用户ID",
    )

    recorder_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="记录人姓名",
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
        comment="外部系统ID",
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
        back_populates="meeting_minutes",
    )

    def __repr__(self) -> str:
        return f"<MeetingMinutes(id={self.id}, title={self.meeting_title}, date={self.meeting_date})>"