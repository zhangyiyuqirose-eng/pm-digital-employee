"""
PM Digital Employee - Document Parse Record Model
项目经理数字员工系统 - 文档解析记录实体模型

v1.3.0新增：记录每次文档解析的完整过程信息
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class DocumentParseRecord(Base):
    """
    文档解析记录实体.

    记录每次文档解析的完整过程信息，包括文件信息、分类结果、提取数据、处理状态等。

    Attributes:
        id: 解析记录唯一标识
        file_key: 飞书文件Key
        file_name: 文件名
        file_type: 文件类型（file/image）
        file_size: 文件大小（字节）
        file_extension: 文件扩展名
        storage_path: 本地存储路径
        document_category: 文档大类
        document_subtype: 文档子类型
        project_phase: 项目阶段
        classification_confidence: 分类置信度
        inferred_project_id: 推断的项目ID
        inferred_project_name: 推断的项目名称
        project_match_type: 项目匹配类型
        confirmed_project_id: 用户确认的项目ID
        entity_types: 可提取实体类型（JSON）
        extracted_data: 提取数据（JSON）
        extraction_confidence: 提取置信度
        field_confidences: 字段置信度（JSON）
        missing_fields: 缺失字段（JSON）
        parse_status: 解析状态
        import_status: 入库状态
        imported_entity_ids: 已入库实体ID（JSON）
        conflict_ids: 冲突记录ID（JSON）
        requires_confirmation: 是否需要确认
        confirmed_by_id: 确认人飞书ID
        confirmed_by_name: 确认人姓名
        confirmed_at: 确认时间
        confirmation_action: 确认动作
        parser_version: 解析器版本
        llm_model: LLM模型
        llm_tokens_input: LLM输入Token
        llm_tokens_output: LLM输出Token
        processing_time_ms: 处理耗时（毫秒）
        error_type: 错误类型
        error_message: 错误信息
        retry_count: 重试次数
        sender_id: 发送者飞书ID
        sender_name: 发送者姓名
        chat_id: 会话ID
        chat_type: 会话类型（p2p/group）
        message_id: 飞书消息ID
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "document_parse_records"
    __table_args__ = (
        Index("ix_document_parse_records_file_key", "file_key"),
        Index("ix_document_parse_records_inferred_project_id", "inferred_project_id"),
        Index("ix_document_parse_records_parse_status", "parse_status"),
        Index("ix_document_parse_records_sender_id", "sender_id"),
        Index("ix_document_parse_records_created_at", "created_at"),
        Index("ix_document_parse_records_requires_confirmation", "requires_confirmation"),
        {"comment": "文档解析记录表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="解析记录ID",
    )

    # 文件信息
    file_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="飞书文件Key",
    )

    file_name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="文件名",
    )

    file_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="文件类型（file/image）",
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="文件大小（字节）",
    )

    file_extension: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="文件扩展名",
    )

    storage_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="本地存储路径",
    )

    # 分类结果
    document_category: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="文档大类",
    )

    document_subtype: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="文档子类型",
    )

    project_phase: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="项目阶段",
    )

    classification_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="分类置信度",
    )

    # 项目关联
    inferred_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="推断的项目ID",
    )

    inferred_project_name: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True,
        comment="推断的项目名称",
    )

    project_match_type: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="项目匹配类型",
    )

    confirmed_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="用户确认的项目ID",
    )

    # 提取结果
    entity_types: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="可提取实体类型（JSON数组）",
    )

    extracted_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="提取数据（JSON）",
    )

    extraction_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="提取置信度",
    )

    field_confidences: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="字段置信度（JSON）",
    )

    missing_fields: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="缺失字段（JSON数组）",
    )

    # 处理状态
    parse_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="解析状态",
    )

    import_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        comment="入库状态",
    )

    imported_entity_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="已入库实体ID（JSON数组）",
    )

    conflict_ids: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="冲突记录ID（JSON数组）",
    )

    # 用户确认
    requires_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否需要确认",
    )

    confirmed_by_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="确认人飞书用户ID",
    )

    confirmed_by_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="确认人姓名",
    )

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="确认时间",
    )

    confirmation_action: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="确认动作",
    )

    # 处理元数据
    parser_version: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="v1.0.0",
        comment="解析器版本",
    )

    llm_model: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="LLM模型名称",
    )

    llm_tokens_input: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="LLM输入Token数",
    )

    llm_tokens_output: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="LLM输出Token数",
    )

    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="处理耗时（毫秒）",
    )

    # 异常信息
    error_type: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="错误类型",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="重试次数",
    )

    # 来源信息
    sender_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="发送者飞书用户ID",
    )

    sender_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="发送者姓名",
    )

    chat_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="会话ID",
    )

    chat_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="会话类型（p2p/group）",
    )

    message_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="飞书消息ID",
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

    def __repr__(self) -> str:
        return f"<DocumentParseRecord(id={self.id}, file={self.file_name}, status={self.parse_status})>"