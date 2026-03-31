"""
PM Digital Employee - Vector Indexer
项目经理数字员工系统 - 向量索引模块

实现文档向量索引、存储、更新、删除。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_gateway import get_llm_gateway
from app.core.config import settings
from app.core.exceptions import ErrorCode, IndexingError
from app.core.logging import get_logger
from app.domain.models.knowledge import KnowledgeDocument
from app.rag.chunker import ChunkerFactory, chunk_document
from app.rag.schemas import (
    ChunkStrategy,
    DocumentChunk,
    DocumentStatus,
    DocumentScopeType,
    IndexRequest,
    IndexResponse,
)

logger = get_logger(__name__)


class VectorIndexer:
    """
    向量索引器.

    实现文档向量索引、存储、更新、删除。
    支持批量索引和增量更新。
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        embedding_batch_size: int = 100,
    ) -> None:
        """
        初始化索引器.

        Args:
            session: 数据库会话
            embedding_batch_size: Embedding批量大小
        """
        self._session = session
        self._embedding_batch_size = embedding_batch_size
        self._llm_gateway = get_llm_gateway()

    async def index_document(
        self,
        request: IndexRequest,
    ) -> IndexResponse:
        """
        索引文档.

        Args:
            request: 索引请求

        Returns:
            IndexResponse: 索引响应
        """
        try:
            # 切片
            chunks = chunk_document(
                content=request.content,
                strategy=request.chunk_strategy,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                metadata={
                    "document_id": str(request.document_id),
                    "scope_type": request.scope_type.value,
                    "scope_id": request.scope_id,
                    **request.metadata,
                },
            )

            if not chunks:
                return IndexResponse(
                    document_id=request.document_id,
                    chunk_count=0,
                    status=DocumentStatus.INDEXED,
                )

            # 生成Embedding
            await self._generate_embeddings(chunks)

            # 存储到数据库
            if self._session:
                await self._store_chunks(chunks, request)

            logger.info(
                "Document indexed",
                document_id=str(request.document_id),
                chunk_count=len(chunks),
            )

            return IndexResponse(
                document_id=request.document_id,
                chunk_count=len(chunks),
                status=DocumentStatus.INDEXED,
            )

        except Exception as e:
            logger.error(
                "Document indexing failed",
                document_id=str(request.document_id),
                error=str(e),
            )

            return IndexResponse(
                document_id=request.document_id,
                chunk_count=0,
                status=DocumentStatus.FAILED,
                error_message=str(e),
            )

    async def index_batch(
        self,
        requests: List[IndexRequest],
    ) -> List[IndexResponse]:
        """
        批量索引文档.

        Args:
            requests: 索引请求列表

        Returns:
            List[IndexResponse]: 索引响应列表
        """
        responses = []

        for request in requests:
            response = await self.index_document(request)
            responses.append(response)

        return responses

    async def delete_document(
        self,
        document_id: uuid.UUID,
    ) -> bool:
        """
        删除文档索引.

        Args:
            document_id: 文档ID

        Returns:
            bool: 是否成功
        """
        if not self._session:
            logger.warning("No database session, cannot delete document")
            return False

        try:
            # 删除所有切片
            await self._session.execute(
                delete(KnowledgeDocument).where(
                    KnowledgeDocument.document_id == document_id,
                ),
            )
            await self._session.commit()

            logger.info(
                "Document index deleted",
                document_id=str(document_id),
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to delete document index",
                document_id=str(document_id),
                error=str(e),
            )
            return False

    async def update_document(
        self,
        request: IndexRequest,
    ) -> IndexResponse:
        """
        更新文档索引.

        Args:
            request: 索引请求

        Returns:
            IndexResponse: 索引响应
        """
        # 先删除旧索引
        await self.delete_document(request.document_id)

        # 重新索引
        return await self.index_document(request)

    async def _generate_embeddings(
        self,
        chunks: List[DocumentChunk],
    ) -> None:
        """
        生成切片的向量Embedding.

        Args:
            chunks: 切片列表
        """
        texts = [chunk.content for chunk in chunks]

        # 批量生成Embedding
        for i in range(0, len(texts), self._embedding_batch_size):
            batch_texts = texts[i:i + self._embedding_batch_size]
            batch_chunks = chunks[i:i + self._embedding_batch_size]

            for text, chunk in zip(batch_texts, batch_chunks):
                try:
                    embedding = await self._llm_gateway.get_embedding(text)
                    chunk.embedding = embedding
                except Exception as e:
                    logger.warning(
                        "Failed to generate embedding for chunk",
                        chunk_id=str(chunk.id),
                        error=str(e),
                    )
                    chunk.embedding = None

    async def _store_chunks(
        self,
        chunks: List[DocumentChunk],
        request: IndexRequest,
    ) -> None:
        """
        存储切片到数据库.

        Args:
            chunks: 切片列表
            request: 索引请求
        """
        if not self._session:
            return

        for chunk in chunks:
            # 创建KnowledgeDocument记录
            # 注意：这里使用KnowledgeDocument作为切片存储
            # 实际项目中可能需要单独的切片表
            doc = KnowledgeDocument(
                id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                embedding=chunk.embedding,
                scope_type=request.scope_type.value,
                scope_id=request.scope_id,
                metadata_=chunk.metadata,
                created_at=datetime.now(timezone.utc),
            )

            self._session.add(doc)

        await self._session.commit()

    async def get_document_chunks(
        self,
        document_id: uuid.UUID,
    ) -> List[DocumentChunk]:
        """
        获取文档的所有切片.

        Args:
            document_id: 文档ID

        Returns:
            List[DocumentChunk]: 切片列表
        """
        if not self._session:
            return []

        result = await self._session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.document_id == document_id,
            ).order_by(KnowledgeDocument.created_at),
        )

        docs = result.scalars().all()

        return [
            DocumentChunk(
                id=doc.id,
                document_id=doc.document_id,
                content=doc.content,
                embedding=doc.embedding,
                metadata=doc.metadata_ or {},
            )
            for doc in docs
        ]

    async def get_index_stats(
        self,
        scope_type: Optional[DocumentScopeType] = None,
        scope_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取索引统计信息.

        Args:
            scope_type: 范围类型
            scope_id: 范围ID

        Returns:
            Dict: 统计信息
        """
        if not self._session:
            return {}

        query = select(KnowledgeDocument)

        if scope_type:
            query = query.where(KnowledgeDocument.scope_type == scope_type.value)
        if scope_id:
            query = query.where(KnowledgeDocument.scope_id == scope_id)

        result = await self._session.execute(query)
        docs = result.scalars().all()

        return {
            "total_chunks": len(docs),
            "unique_documents": len(set(d.document_id for d in docs)),
            "scope_type": scope_type.value if scope_type else None,
            "scope_id": scope_id,
        }


class IncrementalIndexer(VectorIndexer):
    """
    增量索引器.

    支持增量更新和变更检测。
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        embedding_batch_size: int = 100,
    ) -> None:
        """
        初始化增量索引器.

        Args:
            session: 数据库会话
            embedding_batch_size: Embedding批量大小
        """
        super().__init__(session, embedding_batch_size)
        self._content_hashes: Dict[uuid.UUID, str] = {}

    def _compute_hash(
        self,
        content: str,
    ) -> str:
        """
        计算内容哈希.

        Args:
            content: 内容

        Returns:
            str: 哈希值
        """
        import hashlib
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def check_content_changed(
        self,
        document_id: uuid.UUID,
        new_content: str,
    ) -> bool:
        """
        检查内容是否变更.

        Args:
            document_id: 文档ID
            new_content: 新内容

        Returns:
            bool: 是否变更
        """
        new_hash = self._compute_hash(new_content)

        if self._session:
            # 从数据库获取现有文档
            result = await self._session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.document_id == document_id,
                ).limit(1),
            )
            doc = result.scalar_one_or_none()

            if doc:
                old_hash = doc.metadata_.get("content_hash", "")
                return old_hash != new_hash

        return True

    async def index_if_changed(
        self,
        request: IndexRequest,
    ) -> IndexResponse:
        """
        如果内容变更则索引.

        Args:
            request: 索引请求

        Returns:
            IndexResponse: 索引响应
        """
        content_hash = self._compute_hash(request.content)
        request.metadata["content_hash"] = content_hash

        changed = await self.check_content_changed(
            request.document_id,
            request.content,
        )

        if not changed:
            return IndexResponse(
                document_id=request.document_id,
                chunk_count=0,
                status=DocumentStatus.INDEXED,
            )

        return await self.index_document(request)


# 全局索引器实例
_vector_indexer: Optional[VectorIndexer] = None


def get_vector_indexer() -> VectorIndexer:
    """获取向量索引器实例."""
    global _vector_indexer
    if _vector_indexer is None:
        _vector_indexer = VectorIndexer()
    return _vector_indexer


def init_vector_indexer(session: AsyncSession) -> VectorIndexer:
    """初始化向量索引器（带数据库会话）."""
    global _vector_indexer
    _vector_indexer = VectorIndexer(session=session)
    return _vector_indexer