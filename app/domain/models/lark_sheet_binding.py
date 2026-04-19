"""
PM Digital Employee - Lark Sheet Binding Model
项目经理数字员工系统 - 飞书在线表格绑定配置实体模型

v1.2.0新增：飞书在线表格与系统字段映射配置
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base

if TYPE_CHECKING:
    from app.domain.models.project import Project


class LarkSheetBinding(Base):
    """
    飞书在线表格绑定配置实体.
    
    配置飞书在线表格与系统模块的字段映射关系，
    支持双向数据同步。

    Attributes:
        id: 绑定配置唯一标识
        project_id: 项目ID
        lark_sheet_token: 飞书在线表格Token
        lark_sheet_id: 工作表ID
        lark_sheet_name: 工作表名称
        module: 绑定的功能模块
        field_mappings: 字段映射配置（JSON）
        sync_mode: 同步模式
        sync_frequency: 同步频率
        sync_enabled: 是否启用同步
        data_range_start: 数据起始行
        data_range_end: 数据结束范围
        status: 绑定状态
        last_sync_at: 最后同步时间
        last_sync_status: 最后同步状态
        created_by_id: 创建者飞书用户ID
        created_by_name: 创建者姓名
    """

    __tablename__ = "lark_sheet_bindings"
    __table_args__ = (
        Index("ix_lark_sheet_bindings_project_id", "project_id"),
        Index("ix_lark_sheet_bindings_module", "module"),
        Index("ix_lark_sheet_bindings_sync_enabled", "sync_enabled"),
        Index("ix_lark_sheet_bindings_status", "status"),
        {"comment": "飞书在线表格绑定配置表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="绑定配置ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID",
    )

    # 飞书表格信息
    lark_sheet_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="飞书在线表格Token",
    )

    lark_sheet_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="工作表ID",
    )

    lark_sheet_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="工作表名称",
    )

    # 模块信息
    module: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="绑定的功能模块",
    )

    # 字段映射配置
    # 格式: {"A": "name", "B": "code", "C": "start_date", ...}
    field_mappings: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="字段映射配置（JSON）",
    )

    # 同步配置
    sync_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="bidirectional",
        comment="同步模式（to_sheet/from_sheet/bidirectional）",
    )

    sync_frequency: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="realtime",
        comment="同步频率（realtime/5min/15min/1hour）",
    )

    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用同步",
    )

    # 范围配置
    data_range_start: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="数据起始行（如A2）",
    )

    data_range_end: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="数据结束范围",
    )

    # 状态
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        comment="绑定状态（active/inactive/error）",
    )

    # 同步状态
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后同步时间",
    )

    last_sync_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="最后同步状态",
    )

    # 创建者信息
    created_by_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="创建者飞书用户ID",
    )

    created_by_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="创建者姓名",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="lark_sheet_bindings",
    )

    def __repr__(self) -> str:
        return f"<LarkSheetBinding(id={self.id}, module={self.module}, enabled={self.sync_enabled})>"