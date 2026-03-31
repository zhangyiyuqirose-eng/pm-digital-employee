"""
PM Digital Employee - Knowledge Document Model
项目经理数字员工系统 - 知识库文档实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base
from app.domain.enums import KnowledgeScopeType

# pgvector导入
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None


class KnowledgeDocument(Base):
    """
    知识库文档实体.

    存储知识库文档内容和向量嵌入。

    Attributes:
        id: 文档ID
        title: 文档标题
        content: 文档内容
        content_type: 内容类型
        scope_type: 可见范围类型
        department_id: 部门ID（部门可见时）
        project_id: 项目ID（项目可见时）
        embedding: 向量嵌入
        source_url: 来源URL
        doc_type: 文档类型
    """

    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_documents_scope_type", "scope_type"),
        Index("ix_knowledge_documents_department_id", "department_id"),
        Index("ix_knowledge_documents_project_id", "project_id"),
        Index("ix_knowledge_documents_doc_type", "doc_type"),
        Index("ix_knowledge_documents_is_active", "is_active"),
        {"comment": "知识库文档表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="文档ID",
    )

    # 基本信息
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="文档标题",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="文档内容",
    )

    content_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="内容类型",
    )

    # 权限范围
    scope_type: Mapped[KnowledgeScopeType] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeScopeType.PUBLIC,
        index=True,
        comment="可见范围类型",
    )

    department_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="部门ID",
    )

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="项目ID",
    )

    # 向量嵌入（1536维，适配OpenAI embedding）
    embedding: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="向量嵌入（JSON存储，实际使用时转换为pgvector）",
    )

    # 来源信息
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="来源URL",
    )

    source_file: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="来源文件名",
    )

    doc_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="文档类型",
    )

    # 元数据
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="元数据（JSON）",
    )

    # 章节信息（用于定位）
    section_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="章节路径",
    )

    chunk_index: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="切片序号",
    )

    parent_doc_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="父文档ID",
    )

    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效",
    )

    # 版本
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="版本号",
    )

    def __repr__(self) -> str:
        return f"<KnowledgeDocument(id={self.id}, title={self.title})>"


class RetrievalTrace(Base):
    """
    RAG检索轨迹实体.

    记录每次RAG检索的完整信息。

    Attributes:
        id: 轨迹ID
        trace_id: 追踪ID
        query: 查询文本
        user_id: 用户ID
        project_id: 项目ID
        hits: 命中文档列表（JSON）
        latency_ms: 检索耗时
    """

    __tablename__ = "retrieval_traces"
    __table_args__ = (
        Index("ix_retrieval_traces_trace_id", "trace_id"),
        Index("ix_retrieval_traces_user_id", "user_id"),
        Index("ix_retrieval_traces_project_id", "project_id"),
        Index("ix_retrieval_traces_created_at", "created_at"),
        {"comment": "RAG检索轨迹表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="轨迹ID",
    )

    # 追踪
    trace_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="追踪ID",
    )

    # 查询信息
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="查询文本",
    )

    query_embedding_preview: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="查询向量预览",
    )

    # 用户信息
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="用户飞书ID",
    )

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="项目ID",
    )

    # 检索参数
    top_k: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Top-K参数",
    )

    similarity_threshold: Mapped[Optional[float]] = mapped_column(
        None,
        nullable=True,
        comment="相似度阈值",
    )

    # 检索结果
    hits: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="命中文档列表（JSON）",
    )

    hit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="命中数量",
    )

    # 性能
    latency_ms: Mapped[Optional[float]] = mapped_column(
        None,
        nullable=True,
        comment="检索耗时（毫秒）",
    )

    embedding_latency_ms: Mapped[Optional[float]] = mapped_column(
        None,
        nullable=True,
        comment="向量化耗时（毫秒）",
    )

    rerank_latency_ms: Mapped[Optional[float]] = mapped_column(
        None,
        nullable=True,
        comment="重排耗时（毫秒）",
    )

    # 权限过滤
    permission_filtered_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="权限过滤数量",
    )

    def __repr__(self) -> str:
        return f"<RetrievalTrace(id={self.id}, query={self.query[:50]}...)>"