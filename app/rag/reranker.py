"""
PM Digital Employee - Reranker
项目经理数字员工系统 - 重排序模块

对检索结果进行重排序，提升相关性。
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.ai.llm_gateway import get_llm_gateway
from app.core.config import settings
from app.core.logging import get_logger
from app.rag.schemas import RerankRequest, RerankResult, RetrievedDocument

logger = get_logger(__name__)


class BaseReranker(ABC):
    """
    重排序基类.
    """

    @abstractmethod
    async def rerank(
        self,
        request: RerankRequest,
    ) -> RerankResult:
        """
        执行重排序.

        Args:
            request: 重排序请求

        Returns:
            RerankResult: 重排序结果
        """
        pass


class CrossEncoderReranker(BaseReranker):
    """
    交叉编码器重排序器.

    使用LLM进行Query-Document相关性评分。
    """

    def __init__(self) -> None:
        """初始化重排序器."""
        self._llm_gateway = get_llm_gateway()

    async def rerank(
        self,
        request: RerankRequest,
    ) -> RerankResult:
        """
        使用LLM重排序.

        Args:
            request: 重排序请求

        Returns:
            RerankResult: 重排序结果
        """
        start_time = time.time()

        # 对每个文档计算相关性分数
        scored_docs = []

        for doc in request.documents:
            score = await self._compute_relevance_score(
                query=request.query,
                document_content=doc.content,
            )

            # 更新分数
            doc.score = score
            scored_docs.append(doc)

        # 排序
        scored_docs.sort(key=lambda x: x.score, reverse=True)

        # 取top_k
        result_docs = scored_docs[:request.top_k]

        latency_ms = int((time.time() - start_time) * 1000)

        logger.debug(
            "Cross-encoder reranking completed",
            query=request.query[:50],
            input_count=len(request.documents),
            output_count=len(result_docs),
            latency_ms=latency_ms,
        )

        return RerankResult(
            documents=result_docs,
            latency_ms=latency_ms,
        )

    async def _compute_relevance_score(
        self,
        query: str,
        document_content: str,
    ) -> float:
        """
        计算相关性分数.

        Args:
            query: 查询
            document_content: 文档内容

        Returns:
            float: 相关性分数（0-1）
        """
        prompt = f"""请评估以下文档内容与用户查询的相关性。

用户查询：{query}

文档内容：
{document_content[:500]}

请给出一个0到1之间的相关性分数：
- 1.0：完全相关，文档直接回答了查询
- 0.7-0.9：高度相关，文档包含大部分所需信息
- 0.4-0.6：部分相关，文档包含一些相关信息
- 0.1-0.3：低相关，文档与查询关系不大
- 0.0：不相关

请只输出分数数字（如：0.85），不要输出其他内容。
"""

        try:
            response = await self._llm_gateway.generate(
                prompt=prompt,
                max_tokens=10,
                temperature=0.0,
            )

            score_text = response.content.strip()

            # 解析分数
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))
            except ValueError:
                # 尝试提取数字
                import re
                match = re.search(r"[\d.]+", score_text)
                if match:
                    score = float(match.group())
                    return max(0.0, min(1.0, score))
                return 0.5

        except Exception as e:
            logger.warning(
                "Failed to compute relevance score",
                error=str(e),
            )
            return 0.5


class DiversityReranker(BaseReranker):
    """
    多样性重排序器.

    在保证相关性的同时增加结果多样性。
    """

    def __init__(
        self,
        diversity_threshold: float = 0.7,
    ) -> None:
        """
        初始化.

        Args:
            diversity_threshold: 多样性阈值
        """
        self._diversity_threshold = diversity_threshold

    async def rerank(
        self,
        request: RerankRequest,
    ) -> RerankResult:
        """
        多样性重排序.

        Args:
            request: 重排序请求

        Returns:
            RerankResult: 重排序结果
        """
        start_time = time.time()

        # 按原始分数排序
        sorted_docs = sorted(
            request.documents,
            key=lambda x: x.score,
            reverse=True,
        )

        # 选择多样化结果
        selected: List[RetrievedDocument] = []

        for doc in sorted_docs:
            if len(selected) >= request.top_k:
                break

            # 检查与已选文档的相似度
            is_diverse = True

            for selected_doc in selected:
                similarity = self._compute_text_similarity(
                    doc.content,
                    selected_doc.content,
                )

                if similarity > self._diversity_threshold:
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(doc)

        latency_ms = int((time.time() - start_time) * 1000)

        return RerankResult(
            documents=selected,
            latency_ms=latency_ms,
        )

    def _compute_text_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        计算文本相似度（Jaccard）.

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            float: 相似度
        """
        # 简单的词级别Jaccard相似度
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class HybridReranker(BaseReranker):
    """
    混合重排序器.

    结合多种重排序策略。
    """

    def __init__(self) -> None:
        """初始化."""
        self._cross_encoder = CrossEncoderReranker()
        self._diversity_reranker = DiversityReranker()

    async def rerank(
        self,
        request: RerankRequest,
    ) -> RerankResult:
        """
        混合重排序.

        Args:
            request: 重排序请求

        Returns:
            RerankResult: 重排序结果
        """
        # 第一阶段：交叉编码器重排序
        ce_result = await self._cross_encoder.rerank(request)

        # 第二阶段：多样性重排序
        diversity_request = RerankRequest(
            query=request.query,
            documents=ce_result.documents,
            top_k=request.top_k,
        )

        return await self._diversity_reranker.rerank(diversity_request)


class RerankerFactory:
    """
    重排序器工厂.
    """

    _rerankers: Dict[str, type] = {
        "cross_encoder": CrossEncoderReranker,
        "diversity": DiversityReranker,
        "hybrid": HybridReranker,
    }

    @classmethod
    def create(
        cls,
        name: str = "hybrid",
    ) -> BaseReranker:
        """
        创建重排序器.

        Args:
            name: 重排序器名称

        Returns:
            BaseReranker: 重排序器实例
        """
        reranker_class = cls._rerankers.get(name)
        if reranker_class is None:
            raise ValueError(f"Unknown reranker: {name}")
        return reranker_class()


# 全局重排序器实例
_reranker: Optional[BaseReranker] = None


def get_reranker() -> BaseReranker:
    """获取重排序器实例."""
    global _reranker
    if _reranker is None:
        _reranker = HybridReranker()
    return _reranker


async def rerank_documents(
    query: str,
    documents: List[RetrievedDocument],
    top_k: int = 5,
) -> List[RetrievedDocument]:
    """
    便捷函数：重排序文档.

    Args:
        query: 查询
        documents: 文档列表
        top_k: 返回数量

    Returns:
        List[RetrievedDocument]: 重排序后的文档
    """
    reranker = get_reranker()
    request = RerankRequest(
        query=query,
        documents=documents,
        top_k=top_k,
    )
    result = await reranker.rerank(request)
    return result.documents