"""
PM Digital Employee - Policy QA Skill
项目经理数字员工系统 - 制度规范问答Skill

回答项目管理规章制度相关问题，基于RAG检索并引用来源。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_policy_qa_manifest
from app.rag.qa_service import get_policy_qa_service, PolicyQAService
from app.rag.schemas import RAGRequest
from app.skills.base import BaseSkill


class PolicyQASkill(BaseSkill):
    """
    制度规范问答Skill.

    回答项目管理规章制度相关问题。
    """

    skill_name = "policy_qa"
    display_name = "项目制度规范答疑"
    description = "回答项目管理规章制度相关问题，基于知识库检索并引用来源。用户可以输入'管理制度'、'流程规范'、'XX规定'等触发。"
    version = "1.0.0"

    def __init__(
        self,
        manifest: Optional[SkillManifest] = None,
        context: Optional[SkillExecutionContext] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """初始化."""
        super().__init__(manifest, context, session)
        self._qa_service = get_policy_qa_service()

    async def execute(self) -> SkillExecutionResult:
        """
        执行Skill.

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 获取用户问题
        question = self.get_param("question")

        if not question:
            return self.build_error_result("请提供您的问题")

        # 构建RAG请求
        rag_request = RAGRequest(
            query=question,
            user_id=self.user_id,
            project_id=self.project_id,
            top_k=5,
            min_score=0.5,
            include_sources=True,
            max_context_length=4000,
        )

        # 执行问答
        response = await self._qa_service.answer(rag_request)

        # 构建展示数据
        presentation_data = {
            "text": response.answer,
        }

        # 如果有来源，添加到展示数据
        if response.sources:
            sources_text = "\n\n**参考来源：**\n"
            for i, source in enumerate(response.sources, 1):
                sources_text += f"{i}. {source.document_name}\n"

            presentation_data["text"] += sources_text

        # 如果有免责声明，添加
        if response.disclaimer:
            presentation_data["text"] += f"\n\n{response.disclaimer}"

        return self.build_success_result(
            output={
                "answer": response.answer,
                "sources": [
                    {
                        "document_id": str(s.document_id),
                        "document_name": s.document_name,
                        "score": s.score,
                    }
                    for s in response.sources
                ],
                "confidence": response.confidence,
            },
            presentation_type="text",
            presentation_data=presentation_data,
        )

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        return get_policy_qa_manifest()