"""
PM Digital Employee - Data Conflict Model
项目经理数字员工系统 - 数据冲突记录实体模型

v1.2.0新增：记录多源数据同步时的冲突信息
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class DataConflict(Base):
    """
    数据冲突记录实体.
    
    记录多源数据同步时发生的冲突信息，支持人工解决冲突。

    Attributes:
        id: 冲突记录唯一标识
        entity_type: 实体类型
        entity_id: 实体ID
        source_a: 来源A
        source_b: 来源B
        data_a: 来源A的数据（JSON）
        data_b: 来源B的数据（JSON）
        conflict_time: 冲突发生时间
        resolution_status: 解决状态
        resolution_strategy: 解决策略
        resolved_data: 解决后的数据（JSON）
        resolved_at: 解决时间
        resolved_by_id: 解决人飞书用户ID
        resolved_by_name: 解决人姓名
        resolution_notes: 解决备注
    """

    __tablename__ = "data_conflicts"
    __table_args__ = (
        Index("ix_data_conflicts_entity_type", "entity_type"),
        Index("ix_data_conflicts_entity_id", "entity_id"),
        Index("ix_data_conflicts_resolution_status", "resolution_status"),
        Index("ix_data_conflicts_conflict_time", "conflict_time"),
        {"comment": "数据冲突记录表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="冲突记录ID",
    )

    # 冲突信息
    entity_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="实体类型",
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="实体ID",
    )

    # 冲突来源
    source_a: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="来源A（如excel_import）",
    )

    source_b: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="来源B（如lark_sheet_sync）",
    )

    # 冲突数据
    data_a: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="来源A的数据（JSON）",
    )

    data_b: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="来源B的数据（JSON）",
    )

    # 冲突时间
    conflict_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="冲突发生时间",
    )

    # 解决状态
    resolution_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="解决状态（pending/resolved/manual_review）",
    )

    resolution_strategy: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="解决策略（last_write/source_a/source_b/manual）",
    )

    # 解决后的数据
    resolved_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="最终确定的数据（JSON）",
    )

    # 解决信息
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间",
    )

    resolved_by_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="解决人飞书用户ID",
    )

    resolved_by_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="解决人姓名",
    )

    # 备注
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="解决备注",
    )

    def __repr__(self) -> str:
        return f"<DataConflict(id={self.id}, entity={self.entity_type}:{self.entity_id}, status={self.resolution_status})>"