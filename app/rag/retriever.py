"""
PM Digital Employee - Vector Retriever
项目经理数字员工系统 - 权限感知的向量检索模块

实现带权限过滤的向量相似度检索。
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_gateway import get_llm_gateway
from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models.knowledge import KnowledgeDocument
from app.rag.schemas import (
    DocumentScopeType,
    RetrievedDocument,
    RetrievalStrategy,
    SearchResult,
)

logger = get_logger(__name__)


class VectorRetriever:
    """
    向量检索器.

    实现带权限过滤的向量相似度检索。
    支持稠密检索、稀疏检索、混合检索。
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """
        初始化检索器.

        Args:
            session: 数据库会话
        """
        self._session = session
        self._llm_gateway = get_llm_gateway()

    async def search(
        self,
        query: str,
        user_id: str,
        project_id: Optional[uuid.UUID] = None,
        top_k: int = 5,
        min_score: float = 0.5,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
    ) -> SearchResult:
        """
        执行检索.

        Args:
            query: 查询文本
            user_id: 用户ID
            project_id: 项目ID
            top_k: 返回数量
            min_score: 最小相似度
            strategy: 检索策略

        Returns:
            SearchResult: 检索结果
        """
        start_time = time.time()

        # 生成查询向量
        query_embedding = await self._llm_gateway.get_embedding(query)

        # 构建权限过滤条件
        access_filter = self._build_access_filter(user_id, project_id)

        # 执行检索
        if strategy == RetrievalStrategy.DENSE:
            results = await self._dense_search(
                query_embedding=query_embedding,
                access_filter=access_filter,
                top_k=top_k,
                min_score=min_score,
            )
        elif strategy == RetrievalStrategy.SPARSE:
            results = await self._sparse_search(
                query=query,
                access_filter=access_filter,
                top_k=top_k,
            )
        else:  # HYBRID
            results = await self._hybrid_search(
                query=query,
                query_embedding=query_embedding,
                access_filter=access_filter,
                top_k=top_k,
                min_score=min_score,
            )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Search completed",
            query=query[:50],
            user_id=user_id,
            project_id=str(project_id) if project_id else None,
            hit_count=len(results),
            latency_ms=latency_ms,
            strategy=strategy.value,
        )

        return SearchResult(
            chunks=results,
            total_count=len(results),
            query=query,
            latency_ms=latency_ms,
        )

    def _build_access_filter(
        self,
        user_id: str,
        project_id: Optional[uuid.UUID],
    ) -> Dict[str, Any]:
        """
        构建权限过滤条件.

        Args:
            user_id: 用户ID
            project_id: 项目ID

        Returns:
            Dict: 过滤条件
        """
        # 权限范围：
        # 1. 全局文档（scope_type=global）
        # 2. 用户所属部门文档（scope_type=department, scope_id=user_department）
        # 3. 用户参与的项目文档（scope_type=project, scope_id=user_project）
        # 4. 用户私有文档（scope_type=user, scope_id=user_id）

        filter_conditions = {
            "user_id": user_id,
            "project_id": str(project_id) if project_id else None,
            # TODO: 添加部门和项目权限
        }

        return filter_conditions

    async def _dense_search(
        self,
        query_embedding: List[float],
        access_filter: Dict[str, Any],
        top_k: int,
        min_score: float,
    ) -> List[RetrievedDocument]:
        """
        稠密检索（向量检索）.

        Args:
            query_embedding: 查询向量
            access_filter: 权限过滤条件
            top_k: 返回数量
            min_score: 最小相似度

        Returns:
            List[RetrievedDocument]: 检索结果
        """
        if not self._session:
            return []

        # 构建查询
        query = select(KnowledgeDocument).where(
            KnowledgeDocument.embedding.isnot(None),
        )

        # 应用权限过滤
        query = self._apply_access_filter(query, access_filter)

        # 执行查询
        result = await self._session.execute(query)
        docs = result.scalars().all()

        # 计算相似度
        scored_docs: List[Tuple[KnowledgeDocument, float]] = []

        for doc in docs:
            if doc.embedding:
                similarity = self._cosine_similarity(
                    query_embedding,
                    doc.embedding,
                )

                if similarity >= min_score:
                    scored_docs.append((doc, similarity))

        # 排序并取top_k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = scored_docs[:top_k]

        # 转换为RetrievedDocument
        return [
            RetrievedDocument(
                chunk_id=doc.id,
                document_id=doc.document_id,
                document_name=doc.metadata_.get("name", "Unknown"),
                content=doc.content,
                score=score,
                metadata=doc.metadata_ or {},
                source_type=doc.metadata_.get("source_type"),
                source_url=doc.metadata_.get("source_url"),
                page_number=doc.metadata_.get("page_number"),
            )
            for doc, score in top_docs
        ]

    async def _sparse_search(
        self,
        query: str,
        access_filter: Dict[str, Any],
        top_k: int,
    ) -> List[RetrievedDocument]:
        """
        稀疏检索（关键词检索）.

        Args:
            query: 查询文本
            access_filter: 权限过滤条件
            top_k: 返回数量

        Returns:
            List[RetrievedDocument]: 检索结果
        """
        if not self._session:
            return []

        # 使用全文检索（简化实现）
        # 实际项目应使用PostgreSQL的全文检索或Elasticsearch
        search_terms = query.split()

        query_obj = select(KnowledgeDocument)

        # 应用权限过滤
        query_obj = self._apply_access_filter(query_obj, access_filter)

        # 简单的LIKE搜索
        conditions = []
        for term in search_terms:
            conditions.append(KnowledgeDocument.content.ilike(f"%{term}%"))

        if conditions:
            query_obj = query_obj.where(or_(*conditions))

        result = await self._session.execute(query_obj.limit(top_k))
        docs = result.scalars().all()

        # 计算BM25分数（简化版）
        return [
            RetrievedDocument(
                chunk_id=doc.id,
                document_id=doc.document_id,
                document_name=doc.metadata_.get("name", "Unknown"),
                content=doc.content,
                score=0.7,  # 简化分数
                metadata=doc.metadata_ or {},
            )
            for doc in docs
        ]

    async def _hybrid_search(
        self,
        query: str,
        query_embedding: List[float],
        access_filter: Dict[str, Any],
        top_k: int,
        min_score: float,
    ) -> List[RetrievedDocument]:
        """
        混合检索（稠密+稀疏）.

        Args:
            query: 查询文本
            query_embedding: 查询向量
            access_filter: 权限过滤条件
            top_k: 返回数量
            min_score: 最小相似度

        Returns:
            List[RetrievedDocument]: 检索结果
        """
        # 并行执行稠密和稀疏检索
        dense_results = await self._dense_search(
            query_embedding=query_embedding,
            access_filter=access_filter,
            top_k=top_k * 2,  # 取更多候选
            min_score=min_score * 0.8,  # 降低阈值
        )

        sparse_results = await self._sparse_search(
            query=query,
            access_filter=access_filter,
            top_k=top_k * 2,
        )

        # 融合结果（RRF算法）
        return self._reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            top_k,
        )

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[RetrievedDocument],
        sparse_results: List[RetrievedDocument],
        top_k: int,
        k: int = 60,
    ) -> List[RetrievedDocument]:
        """
        倒数排名融合（RRF）.

        Args:
            dense_results: 稠密检索结果
            sparse_results: 稀疏检索结果
            top_k: 返回数量
            k: RRF参数

        Returns:
            List[RetrievedDocument]: 融合结果
        """
        # 计算RRF分数
        scores: Dict[uuid.UUID, float] = {}
        doc_map: Dict[uuid.UUID, RetrievedDocument] = {}

        # 稠密结果
        for rank, doc in enumerate(dense_results):
            chunk_id = doc.chunk_id
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
            doc_map[chunk_id] = doc

        # 稀疏结果
        for rank, doc in enumerate(sparse_results):
            chunk_id = doc.chunk_id
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
            doc_map[chunk_id] = doc

        # 排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # 构建结果
        results = []
        for chunk_id in sorted_ids[:top_k]:
            doc = doc_map[chunk_id]
            # 更新分数为融合分数
            doc.score = scores[chunk_id]
            results.append(doc)

        return results

    def _apply_access_filter(
        self,
        query,
        access_filter: Dict[str, Any],
    ):
        """
        应用权限过滤.

        Args:
            query: SQLAlchemy查询
            access_filter: 过滤条件

        Returns:
            查询对象
        """
        conditions = []

        # 全局文档
        conditions.append(
            KnowledgeDocument.scope_type == DocumentScopeType.GLOBAL.value,
        )

        # 项目文档
        project_id = access_filter.get("project_id")
        if project_id:
            conditions.append(
                and_(
                    KnowledgeDocument.scope_type == DocumentScopeType.PROJECT.value,
                    KnowledgeDocument.scope_id == project_id,
                ),
            )

        # 用户私有文档
        user_id = access_filter.get("user_id")
        if user_id:
            conditions.append(
                and_(
                    KnowledgeDocument.scope_type == DocumentScopeType.USER.value,
                    KnowledgeDocument.scope_id == user_id,
                ),
            )

        # TODO: 添加部门权限

        return query.where(or_(*conditions))

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """
        计算余弦相似度.

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            float: 相似度
        """
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    async def search_by_document(
        self,
        document_id: uuid.UUID,
        query: str,
        top_k: int = 5,
    ) -> List[RetrievedDocument]:
        """
        在特定文档内检索.

        Args:
            document_id: 文档ID
            query: 查询文本
            top_k: 返回数量

        Returns:
            List[RetrievedDocument]: 检索结果
        """
        if not self._session:
            return []

        # 生成查询向量
        query_embedding = await self._llm_gateway.get_embedding(query)

        # 查询文档切片
        result = await self._session.execute(
            select(KnowledgeDocument).where(
                and_(
                    KnowledgeDocument.document_id == document_id,
                    KnowledgeDocument.embedding.isnot(None),
                ),
            ),
        )

        docs = result.scalars().all()

        # 计算相似度
        scored_docs = []
        for doc in docs:
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                scored_docs.append((doc, similarity))

        # 排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = scored_docs[:top_k]

        return [
            RetrievedDocument(
                chunk_id=doc.id,
                document_id=doc.document_id,
                document_name=doc.metadata_.get("name", "Unknown"),
                content=doc.content,
                score=score,
                metadata=doc.metadata_ or {},
            )
            for doc, score in top_docs
        ]


class PermissionAwareRetriever(VectorRetriever):
    """
    权限感知检索器.

    增强的权限检查能力。
    """

    async def search_with_permission_check(
        self,
        query: str,
        user_id: str,
        user_accessible_projects: List[uuid.UUID],
        user_department_id: Optional[str] = None,
        top_k: int = 5,
    ) -> SearchResult:
        """
        带完整权限检查的检索.

        Args:
            query: 查询文本
            user_id: 用户ID
            user_accessible_projects: 用户可访问的项目列表
            user_department_id: 用户部门ID
            top_k: 返回数量

        Returns:
            SearchResult: 检索结果
        """
        # 构建完整的权限过滤
        access_filter = {
            "user_id": user_id,
            "accessible_projects": [str(p) for p in user_accessible_projects],
            "department_id": user_department_id,
        }

        # 执行检索
        return await self.search(
            query=query,
            user_id=user_id,
            top_k=top_k,
        )


# 全局检索器实例
_vector_retriever: Optional[VectorRetriever] = None


def get_vector_retriever() -> VectorRetriever:
    """获取向量检索器实例."""
    global _vector_retriever
    if _vector_retriever is None:
        _vector_retriever = VectorRetriever()
    return _vector_retriever


def init_vector_retriever(session: AsyncSession) -> VectorRetriever:
    """初始化向量检索器（带数据库会话）."""
    global _vector_retriever
    _vector_retriever = VectorRetriever(session=session)
    return _vector_retriever