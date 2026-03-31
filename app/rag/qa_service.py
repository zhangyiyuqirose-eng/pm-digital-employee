"""
PM Digital Employee - RAG QA Service
项目经理数字员工系统 - RAG问答服务

实现基于检索增强生成的问答服务。
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_gateway import get_llm_gateway
from app.ai.safety_guard import get_safety_guard
from app.core.config import settings
from app.core.exceptions import ErrorCode, RAGError
from app.core.logging import get_logger
from app.rag.reranker import get_reranker
from app.rag.retriever import get_vector_retriever
from app.rag.schemas import (
    RAGRequest,
    RAGResponse,
    RetrievedDocument,
    RetrievalStrategy,
    RetrievalTraceRecord,
)

logger = get_logger(__name__)


# RAG回答Prompt模板
RAG_QA_PROMPT = """你是一个专业的项目管理助手。请根据提供的参考资料回答用户问题。

## 重要规则
1. 只使用参考资料中的信息回答问题
2. 如果参考资料中没有相关信息，明确告知用户
3. 回答要准确、专业、简洁
4. 必须在回答中引用来源（使用[来源X]格式）

## 参考资料
{context}

## 用户问题
{question}

## 回答
"""


class RAGQAService:
    """
    RAG问答服务.

    实现检索增强生成的问答流程：
    1. 查询理解
    2. 检索相关文档
    3. 重排序
    4. 生成回答
    5. 后处理
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """
        初始化RAG问答服务.

        Args:
            session: 数据库会话
        """
        self._session = session
        self._llm_gateway = get_llm_gateway()
        self._retriever = get_vector_retriever()
        self._reranker = get_reranker()
        self._safety_guard = get_safety_guard()

    async def answer(
        self,
        request: RAGRequest,
    ) -> RAGResponse:
        """
        回答用户问题.

        Args:
            request: RAG请求

        Returns:
            RAGResponse: RAG响应
        """
        start_time = time.time()

        try:
            # 1. 安全检查
            safety_result = await self._safety_guard.check_prompt_injection(
                request.query,
            )

            if safety_result.is_malicious:
                return RAGResponse(
                    answer="抱歉，您的请求无法处理。",
                    has_answer=False,
                    disclaimer="检测到异常输入",
                )

            # 2. 检索相关文档
            search_result = await self._retriever.search(
                query=request.query,
                user_id=request.user_id,
                project_id=request.project_id,
                top_k=request.top_k * 2,  # 取更多候选
                min_score=request.min_score * 0.8,
                strategy=request.retrieval_strategy,
            )

            if not search_result.chunks:
                # 无相关文档
                return RAGResponse(
                    answer="抱歉，我没有找到与您问题相关的资料。请尝试换个方式提问，或联系管理员添加相关文档。",
                    has_answer=False,
                    sources=[],
                    latency_ms=int((time.time() - start_time) * 1000),
                )

            # 3. 重排序
            reranked_docs = await self._reranker.rerank_documents(
                query=request.query,
                documents=search_result.chunks,
                top_k=request.top_k,
            )

            # 4. 构建上下文
            context, context_length = self._build_context(
                documents=reranked_docs,
                max_length=request.max_context_length,
            )

            # 5. 生成回答
            answer = await self._generate_answer(
                question=request.query,
                context=context,
            )

            # 6. 计算置信度
            confidence = self._calculate_confidence(
                answer=answer,
                documents=reranked_docs,
            )

            # 7. 构建来源列表
            sources = []
            if request.include_sources:
                sources = self._format_sources(reranked_docs)

            # 8. 记录检索轨迹
            await self._log_retrieval_trace(
                query=request.query,
                user_id=request.user_id,
                project_id=request.project_id,
                hits=reranked_docs,
                latency_ms=int((time.time() - start_time) * 1000),
            )

            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "RAG QA completed",
                query=request.query[:50],
                hit_count=len(reranked_docs),
                confidence=confidence,
                latency_ms=latency_ms,
            )

            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                has_answer=True,
                disclaimer=self._get_disclaimer(confidence),
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error(
                "RAG QA failed",
                query=request.query[:50],
                error=str(e),
            )

            return RAGResponse(
                answer="抱歉，处理您的请求时出现错误。请稍后重试。",
                has_answer=False,
                error_message=str(e),
                latency_ms=int((time.time() - start_time) * 1000),
            )

    def _build_context(
        self,
        documents: List[RetrievedDocument],
        max_length: int,
    ) -> tuple:
        """
        构建上下文.

        Args:
            documents: 文档列表
            max_length: 最大长度

        Returns:
            tuple: (上下文字符串, 实际长度)
        """
        context_parts = []
        total_length = 0

        for i, doc in enumerate(documents):
            # 添加来源标记
            source_header = f"\n[来源{i + 1}] {doc.document_name}\n"
            content = doc.content

            chunk_length = len(source_header) + len(content)

            if total_length + chunk_length > max_length:
                # 截断
                remaining = max_length - total_length - len(source_header)
                if remaining > 100:
                    content = content[:remaining] + "..."
                else:
                    break

            context_parts.append(source_header + content)
            total_length += chunk_length

        return "\n".join(context_parts), total_length

    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        生成回答.

        Args:
            question: 用户问题
            context: 上下文

        Returns:
            str: 生成的回答
        """
        prompt = RAG_QA_PROMPT.format(
            context=context,
            question=question,
        )

        response = await self._llm_gateway.generate(
            prompt=prompt,
            max_tokens=settings.llm.max_tokens,
            temperature=0.3,  # 较低温度以获得更确定性的回答
        )

        return response.content

    def _calculate_confidence(
        self,
        answer: str,
        documents: List[RetrievedDocument],
    ) -> float:
        """
        计算置信度.

        Args:
            answer: 回答
            documents: 文档列表

        Returns:
            float: 置信度
        """
        # 基于文档分数计算
        if not documents:
            return 0.0

        # 平均分数
        avg_score = sum(d.score for d in documents) / len(documents)

        # 文档数量因子
        doc_count_factor = min(1.0, len(documents) / 3.0)

        # 回答中是否包含来源引用
        has_citation = "[来源" in answer

        # 综合置信度
        confidence = avg_score * 0.6 + doc_count_factor * 0.2 + (0.2 if has_citation else 0)

        return min(1.0, confidence)

    def _format_sources(
        self,
        documents: List[RetrievedDocument],
    ) -> List[RetrievedDocument]:
        """
        格式化来源列表.

        Args:
            documents: 文档列表

        Returns:
            List[RetrievedDocument]: 格式化后的来源
        """
        # 去重（按文档ID）
        seen_doc_ids = set()
        unique_sources = []

        for doc in documents:
            if doc.document_id not in seen_doc_ids:
                seen_doc_ids.add(doc.document_id)
                unique_sources.append(doc)

        return unique_sources

    def _get_disclaimer(
        self,
        confidence: float,
    ) -> Optional[str]:
        """
        获取免责声明.

        Args:
            confidence: 置信度

        Returns:
            Optional[str]: 免责声明
        """
        if confidence < 0.5:
            return "⚠️ 此回答的置信度较低，建议您核实相关信息。"

        if confidence < 0.7:
            return "ℹ️ 此回答基于有限的参考资料，建议您进一步确认。"

        return None

    async def _log_retrieval_trace(
        self,
        query: str,
        user_id: str,
        project_id: Optional[uuid.UUID],
        hits: List[RetrievedDocument],
        latency_ms: int,
    ) -> None:
        """
        记录检索轨迹.

        Args:
            query: 查询
            user_id: 用户ID
            project_id: 项目ID
            hits: 命中文档
            latency_ms: 耗时
        """
        trace = RetrievalTraceRecord(
            query=query,
            user_id=user_id,
            project_id=project_id,
            hits=[
                {
                    "chunk_id": str(doc.chunk_id),
                    "document_id": str(doc.document_id),
                    "score": doc.score,
                }
                for doc in hits
            ],
            hit_count=len(hits),
            latency_ms=latency_ms,
        )

        logger.debug(
            "Retrieval trace logged",
            trace_id=str(trace.trace_id),
            query=query[:50],
            hit_count=len(hits),
        )


class PolicyQAService(RAGQAService):
    """
    制度规范问答服务.

    专门用于回答项目管理规章制度相关问题。
    强制要求引用来源。
    """

    # 制度问答专用Prompt
    POLICY_QA_PROMPT = """你是一个项目管理规章制度咨询助手。请根据提供的制度文档回答用户问题。

## 重要规则
1. **必须**只使用制度文档中的信息回答
2. **必须**在回答中明确引用具体的制度条款来源
3. 如果制度文档中没有相关规定，**明确告知**用户"根据现有制度，未找到相关规定"
4. 回答要准确、专业、有依据

## 制度文档
{context}

## 用户问题
{question}

## 回答
（请在回答中注明依据的制度条款，如："根据《XX管理办法》第X条规定：..."）
"""

    async def answer(
        self,
        request: RAGRequest,
    ) -> RAGResponse:
        """
        回答制度问题.

        Args:
            request: RAG请求

        Returns:
            RAGResponse: RAG响应
        """
        # 确保只检索制度类文档
        # TODO: 添加文档类型过滤

        response = await super().answer(request)

        # 检查回答是否有来源引用
        if response.has_answer:
            if "根据" not in response.answer and "规定" not in response.answer:
                # 没有引用来源，添加提示
                response.answer += "\n\n⚠️ 提示：以上回答未找到明确的制度依据，建议您查阅相关制度文件确认。"
                response.confidence *= 0.8

        return response

    async def _generate_answer(
        self,
        question: str,
        context: str,
    ) -> str:
        """生成制度问答回答."""
        prompt = self.POLICY_QA_PROMPT.format(
            context=context,
            question=question,
        )

        response = await self._llm_gateway.generate(
            prompt=prompt,
            max_tokens=settings.llm.max_tokens,
            temperature=0.2,  # 更低温度
        )

        return response.content


# 全局服务实例
_rag_qa_service: Optional[RAGQAService] = None
_policy_qa_service: Optional[PolicyQAService] = None


def get_rag_qa_service() -> RAGQAService:
    """获取RAG问答服务实例."""
    global _rag_qa_service
    if _rag_qa_service is None:
        _rag_qa_service = RAGQAService()
    return _rag_qa_service


def get_policy_qa_service() -> PolicyQAService:
    """获取制度问答服务实例."""
    global _policy_qa_service
    if _policy_qa_service is None:
        _policy_qa_service = PolicyQAService()
    return _policy_qa_service


def init_rag_qa_service(session: AsyncSession) -> RAGQAService:
    """初始化RAG问答服务（带数据库会话）."""
    global _rag_qa_service
    _rag_qa_service = RAGQAService(session=session)
    return _rag_qa_service