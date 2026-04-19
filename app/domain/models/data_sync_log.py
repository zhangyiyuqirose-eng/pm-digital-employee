"""
PM Digital Employee - Data Sync Log Model
项目经理数字员工系统 - 数据同步日志实体模型

v1.2.0新增：记录所有数据同步操作的日志
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class DataSyncLog(Base):
    """
    数据同步日志实体.
    
    记录所有数据同步操作（Excel导入、飞书表格同步、飞书卡片）的详细日志。

    Attributes:
        id: 日志唯一标识
        sync_type: 同步类型（excel_import/lark_sheet/lark_card）
        sync_direction: 同步方向（import/export/bidirectional）
        sync_status: 同步状态（pending/running/success/failed/partial）
        project_id: 项目ID
        module: 功能模块
        records_total: 总记录数
        records_success: 成功记录数
        records_failed: 失败记录数
        records_skipped: 跳过记录数
        error_details: 错误详情（JSON）
        lark_sheet_token: 飞书表格Token
        lark_sheet_range: 飞书表格范围
        excel_file_name: Excel文件名
        excel_file_path: Excel文件路径
        started_at: 开始时间
        completed_at: 完成时间
        duration_ms: 执行耗时（毫秒）
        operator_id: 操作人飞书用户ID
        operator_name: 操作人姓名
    """

    __tablename__ = "data_sync_logs"
    __table_args__ = (
        Index("ix_data_sync_logs_sync_type", "sync_type"),
        Index("ix_data_sync_logs_project_id", "project_id"),
        Index("ix_data_sync_logs_module", "module"),
        Index("ix_data_sync_logs_sync_status", "sync_status"),
        Index("ix_data_sync_logs_created_at", "created_at"),
        {"comment": "数据同步日志表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="日志ID",
    )

    # 同步信息
    sync_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="同步类型（excel_import/lark_sheet/lark_card）",
    )

    sync_direction: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="同步方向（import/export/bidirectional）",
    )

    sync_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="同步状态（pending/running/success/failed/partial）",
    )

    # 项目信息
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="项目ID",
    )

    module: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="功能模块（project/task/wbs/cost/risk等）",
    )

    # 同步数据统计
    records_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总记录数",
    )

    records_success: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="成功记录数",
    )

    records_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="失败记录数",
    )

    records_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="跳过记录数",
    )

    # 错误信息
    error_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误详情（JSON数组）",
    )

    # 飞书表格信息
    lark_sheet_token: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="飞书在线表格Token",
    )

    lark_sheet_range: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="飞书表格范围",
    )

    # Excel文件信息
    excel_file_name: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="Excel文件名",
    )

    excel_file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Excel文件路径",
    )

    # 执行信息
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行耗时（毫秒）",
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

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<DataSyncLog(id={self.id}, type={self.sync_type}, status={self.sync_status})>"