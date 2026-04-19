"""
PM Digital Employee - Data Version Model
项目经理数字员工系统 - 数据版本历史实体模型

v1.2.0新增：支持数据版本记录和回滚
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class DataVersion(Base):
    """
    数据版本历史实体.
    
    记录所有核心数据的版本变更历史，支持回滚和历史版本查询。

    Attributes:
        id: 版本记录唯一标识
        entity_type: 实体类型（project/task/cost/risk等）
        entity_id: 实体ID
        version: 版本号
        operation: 操作类型（create/update/delete）
        data_before: 操作前数据（JSON）
        data_after: 操作后数据（JSON）
        changed_fields: 变更的字段列表（JSON数组）
        data_source: 数据来源
        operator_id: 操作人飞书用户ID
        operator_name: 操作人姓名
        lark_sheet_token: 飞书表格Token（如果来源是飞书表格）
        lark_sheet_row: 飞书表格行号
    """

    __tablename__ = "data_versions"
    __table_args__ = (
        Index("ix_data_versions_entity_type", "entity_type"),
        Index("ix_data_versions_entity_id", "entity_id"),
        Index("ix_data_versions_version", "version"),
        Index("ix_data_versions_data_source", "data_source"),
        Index("ix_data_versions_created_at", "created_at"),
        {"comment": "数据版本历史表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="版本记录ID",
    )

    # 数据引用
    entity_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="实体类型（project/task/cost/risk/milestone等）",
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="实体ID",
    )

    # 版本信息
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="版本号",
    )

    operation: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="操作类型（create/update/delete）",
    )

    # 数据内容
    data_before: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="操作前数据（JSON，仅update/delete）",
    )

    data_after: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="操作后数据（JSON，仅create/update）",
    )

    # 变更字段
    changed_fields: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="变更的字段列表（JSON数组）",
    )

    # 数据来源
    data_source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="数据来源（lark_card/excel_import/lark_sheet_sync）",
    )

    # 操作人
    operator_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="操作人飞书用户ID",
    )

    operator_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="操作人姓名",
    )

    # 飞书表格同步信息
    lark_sheet_token: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="飞书表格Token",
    )

    lark_sheet_row: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="飞书表格行号",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<DataVersion(id={self.id}, entity={self.entity_type}:{self.entity_id}, v={self.version})>"