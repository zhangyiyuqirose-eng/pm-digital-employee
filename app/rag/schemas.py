"""
PM Digital Employee - RAG Schemas
项目经理数字员工系统 - RAG检索层Pydantic模型

定义知识库、向量检索、RAG问答相关的数据结构。
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentScopeType(str, Enum):
    """文档范围类型."""

    GLOBAL = "global"  # 全局可见
    PROJECT = "project"  # 项目级
    DEPARTMENT = "department"  # 部门级
    USER = "user"  # 用户私有


class DocumentStatus(str, Enum):
    """文档状态."""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    INDEXED = "indexed"  # 已索引
    FAILED = "failed"  # 失败


class ChunkStrategy(str, Enum):
    """切片策略."""

    FIXED_SIZE = "fixed_size"  # 固定大小
    SEMANTIC = "semantic"  # 语义切片
    PARAGRAPH = "paragraph"  # 段落切片
    RECURSIVE = "recursive"  # 递归切片


class RetrievalStrategy(str, Enum):
    """检索策略."""

    DENSE = "dense"  # 稠密检索
    SPARSE = "sparse"  # 稀疏检索
    HYBRID = "hybrid"  # 混合检索


class RAGRequest(BaseModel):
    """RAG问答请求."""

    query: str = Field(..., description="用户查询")
    user_id: str = Field(..., description="用户ID")
    project_id: Optional[uuid.UUID] = Field(None, description="项目ID")
    top_k: int = Field(5, ge=1, le=20, description="返回文档数")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="最小相似度")
    retrieval_strategy: RetrievalStrategy = Field(
        RetrievalStrategy.HYBRID,
        description="检索策略",
    )
    include_sources: bool = Field(True, description="是否包含来源")
    max_context_length: int = Field(4000, description="最大上下文长度")


class RetrievedDocument(BaseModel):
    """检索到的文档."""

    chunk_id: uuid.UUID = Field(..., description="切片ID")
    document_id: uuid.UUID = Field(..., description="文档ID")
    document_name: str = Field(..., description="文档名称")
    content: str = Field(..., description="内容")
    score: float = Field(..., ge=0.0, le=1.0, description="相似度分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    source_type: Optional[str] = Field(None, description="来源类型")
    source_url: Optional[str] = Field(None, description="来源URL")
    page_number: Optional[int] = Field(None, description="页码")


class RAGResponse(BaseModel):
    """RAG问答响应."""

    answer: str = Field(..., description="回答内容")
    sources: List[RetrievedDocument] = Field(
        default_factory=list,
        description="来源文档",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    has_answer: bool = Field(True, description="是否有答案")
    disclaimer: Optional[str] = Field(None, description="免责声明")
    tokens_used: int = Field(0, description="消耗的Token数")
    latency_ms: int = Field(0, description="耗时毫秒")


class DocumentChunk(BaseModel):
    """文档切片."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="切片ID",
    )
    document_id: uuid.UUID = Field(..., description="文档ID")
    content: str = Field(..., description="内容")
    chunk_index: int = Field(..., ge=0, description="切片索引")
    embedding: Optional[List[float]] = Field(None, description="向量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class IndexRequest(BaseModel):
    """索引请求."""

    document_id: uuid.UUID = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    scope_type: DocumentScopeType = Field(
        DocumentScopeType.GLOBAL,
        description="范围类型",
    )
    scope_id: Optional[str] = Field(None, description="范围ID")
    chunk_strategy: ChunkStrategy = Field(
        ChunkStrategy.RECURSIVE,
        description="切片策略",
    )
    chunk_size: int = Field(500, description="切片大小")
    chunk_overlap: int = Field(50, description="切片重叠")


class IndexResponse(BaseModel):
    """索引响应."""

    document_id: uuid.UUID = Field(..., description="文档ID")
    chunk_count: int = Field(0, description="切片数量")
    status: DocumentStatus = Field(
        DocumentStatus.INDEXED,
        description="状态",
    )
    error_message: Optional[str] = Field(None, description="错误信息")


class SearchResult(BaseModel):
    """搜索结果."""

    chunks: List[RetrievedDocument] = Field(
        default_factory=list,
        description="切片列表",
    )
    total_count: int = Field(0, description="总数")
    query: str = Field(..., description="查询")
    latency_ms: int = Field(0, description="耗时")


class RerankRequest(BaseModel):
    """重排请求."""

    query: str = Field(..., description="查询")
    documents: List[RetrievedDocument] = Field(
        ...,
        description="待重排文档",
    )
    top_k: int = Field(5, description="返回数量")


class RerankResult(BaseModel):
    """重排结果."""

    documents: List[RetrievedDocument] = Field(
        ...,
        description="重排后的文档",
    )
    latency_ms: int = Field(0, description="耗时")


class KnowledgeDocumentInput(BaseModel):
    """知识库文档输入."""

    name: str = Field(..., description="文档名称")
    content: str = Field(..., description="文档内容")
    source_type: str = Field("file", description="来源类型")
    source_url: Optional[str] = Field(None, description="来源URL")
    scope_type: DocumentScopeType = Field(
        DocumentScopeType.GLOBAL,
        description="范围类型",
    )
    scope_id: Optional[str] = Field(None, description="范围ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class RetrievalTraceRecord(BaseModel):
    """检索轨迹记录."""

    trace_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="追踪ID",
    )
    query: str = Field(..., description="查询")
    user_id: str = Field(..., description="用户ID")
    project_id: Optional[uuid.UUID] = Field(None, description="项目ID")
    hits: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="命中文档",
    )
    hit_count: int = Field(0, description="命中数")
    latency_ms: int = Field(0, description="耗时")
    retrieval_strategy: RetrievalStrategy = Field(
        RetrievalStrategy.HYBRID,
        description="检索策略",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class EmbeddingBatch(BaseModel):
    """Embedding批量请求."""

    texts: List[str] = Field(..., description="文本列表")
    model: str = Field("text-embedding-ada-002", description="模型名称")


class EmbeddingBatchResponse(BaseModel):
    """Embedding批量响应."""

    embeddings: List[List[float]] = Field(..., description="向量列表")
    model: str = Field(..., description="模型名称")
    total_tokens: int = Field(0, description="总Token数")
    latency_ms: int = Field(0, description="耗时")