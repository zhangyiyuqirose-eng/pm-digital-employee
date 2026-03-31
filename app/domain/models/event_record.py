"""
PM Digital Employee - Event Record Model
项目经理数字员工系统 - 事件记录实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base
from app.domain.enums import EventStatus, EventType


class EventRecord(Base):
    """
    事件记录实体.

    存储系统事件的完整信息，用于事件溯源和异步处理。

    Attributes:
        id: 事件ID
        event_id: 事件唯一标识
        event_type: 事件类型
        project_id: 相关项目ID
        source: 事件来源
        data: 事件数据（JSON）
        status: 处理状态
        retry_count: 重试次数
    """

    __tablename__ = "event_records"
    __table_args__ = (
        Index("ix_event_records_event_id", "event_id", unique=True),
        Index("ix_event_records_event_type", "event_type"),
        Index("ix_event_records_project_id", "project_id"),
        Index("ix_event_records_status", "status"),
        Index("ix_event_records_created_at", "created_at"),
        {"comment": "事件记录表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="记录ID",
    )

    # 事件标识
    event_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        comment="事件唯一标识",
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="事件类型",
    )

    # 项目关联
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="相关项目ID",
    )

    # 来源
    source: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="事件来源",
    )

    source_event_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="源事件ID（飞书事件ID等）",
    )

    # 事件数据
    data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="事件数据（JSON）",
    )

    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="事件元数据（JSON）",
    )

    # 用户关联
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="触发用户飞书ID",
    )

    # 处理状态
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=EventStatus.PENDING,
        comment="处理状态",
    )

    # 重试
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="重试次数",
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="最大重试次数",
    )

    # 处理时间
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="处理完成时间",
    )

    # 处理结果
    result: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="处理结果（JSON）",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )

    # 调度信息
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="计划执行时间",
    )

    # 追踪
    trace_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="追踪ID",
    )

    def __repr__(self) -> str:
        return f"<EventRecord(id={self.id}, event_type={self.event_type}, status={self.status})>"

    @property
    def can_retry(self) -> bool:
        """判断是否可以重试."""
        return self.retry_count < self.max_retries and self.status in [
            EventStatus.FAILED,
            EventStatus.RETRY,
        ]