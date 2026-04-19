"""
PM Digital Employee - Excel Import Log Model
项目经理数字员工系统 - Excel导入详细日志实体模型

v1.2.0新增：记录Excel导入操作的详细日志
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class ExcelImportLog(Base):
    """
    Excel导入详细日志实体.
    
    记录每次Excel导入操作的详细信息，包括校验结果、行级错误等。

    Attributes:
        id: 日志唯一标识
        sync_log_id: 关联的数据同步日志ID
        file_name: Excel文件名
        file_path: Excel文件路径
        file_size: 文件大小（字节）
        template_version: 模板版本号
        import_mode: 导入模式（full_replace/incremental_update/append_only）
        validation_passed: 校验是否通过
        validation_errors: 校验错误（JSON数组）
        rows_total: 总行数
        rows_imported: 导入成功行数
        rows_updated: 更新行数
        rows_skipped: 跳过行数
        rows_failed: 失败行数
        row_errors: 行级错误详情（JSON数组）
        import_report_path: 导入报告文件路径
    """

    __tablename__ = "excel_import_logs"
    __table_args__ = (
        Index("ix_excel_import_logs_sync_log_id", "sync_log_id"),
        Index("ix_excel_import_logs_file_name", "file_name"),
        Index("ix_excel_import_logs_validation_passed", "validation_passed"),
        {"comment": "Excel导入详细日志表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="日志ID",
    )

    # 关联的同步日志
    sync_log_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sync_logs.id", ondelete="CASCADE"),
        nullable=True,
        comment="关联的数据同步日志ID",
    )

    # 文件信息
    file_name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Excel文件名",
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Excel文件路径",
    )

    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小（字节）",
    )

    template_version: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="模板版本号",
    )

    # 导入模式
    import_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="导入模式（full_replace/incremental_update/append_only）",
    )

    # 校验结果
    validation_passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="校验是否通过",
    )

    validation_errors: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="校验错误（JSON数组）",
    )

    # 导入统计
    rows_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="总行数",
    )

    rows_imported: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="导入成功行数",
    )

    rows_updated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="更新行数",
    )

    rows_skipped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="跳过行数",
    )

    rows_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="失败行数",
    )

    # 行级错误详情
    row_errors: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="行级错误详情（JSON数组）",
    )

    # 导入报告
    import_report_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="导入报告文件路径",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return f"<ExcelImportLog(id={self.id}, file={self.file_name}, imported={self.rows_imported})>"