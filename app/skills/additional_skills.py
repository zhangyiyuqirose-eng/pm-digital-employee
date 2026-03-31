"""
PM Digital Employee - Additional Skills
项目经理数字员工系统 - 其他核心Skill实现
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_gateway import get_llm_gateway
from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.skills.base import BaseSkill


# ==================== WBS生成Skill ====================

class WBSGenerationSkill(BaseSkill):
    """WBS自动生成Skill."""

    skill_name = "wbs_generation"
    display_name = "WBS自动生成"
    description = "根据项目信息自动生成WBS工作分解结构。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        project_id = self._get_project_id()
        requirements = self.get_param("requirements", "")

        if not project_id:
            return self.build_error_result("请提供项目ID")

        # 获取项目信息
        project_info = await self._get_project_info(project_id)

        # 生成WBS
        wbs_result = await self._generate_wbs(project_info, requirements)

        return self.build_success_result(
            output=wbs_result,
            presentation_type="text",
            presentation_data={
                "text": self._format_wbs_output(wbs_result),
            },
        )

    def _get_project_id(self) -> Optional[uuid.UUID]:
        param = self.get_param("project_id")
        if not param:
            return self.project_id
        try:
            return uuid.UUID(param)
        except ValueError:
            return None

    async def _get_project_info(self, project_id: uuid.UUID) -> Dict:
        """获取项目信息."""
        if not self._session:
            return {
                "name": "示例项目",
                "duration": 180,
                "type": "软件开发",
            }

        from app.domain.models.project import Project

        result = await self._session.execute(
            select(Project).where(Project.id == project_id),
        )
        project = result.scalar_one_or_none()

        if not project:
            return {}

        return {
            "name": project.name,
            "duration": 180,
            "type": "软件开发",
        }

    async def _generate_wbs(self, project_info: Dict, requirements: str) -> Dict:
        """生成WBS."""
        llm_gateway = get_llm_gateway()

        prompt = f"""请为以下项目生成WBS工作分解结构：

项目名称：{project_info.get('name', '未知')}
项目类型：{project_info.get('type', '未知')}
项目周期：{project_info.get('duration', 0)}天
项目需求：{requirements or '通用软件项目'}

请生成3层结构的WBS，包含：
1. 主要阶段（需求、设计、开发、测试、部署）
2. 每个阶段的主要任务
3. 每个任务的预估工期

以JSON格式输出。
"""

        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        return {
            "wbs_content": response.content,
            "project_name": project_info.get("name", ""),
        }

    def _format_wbs_output(self, wbs_result: Dict) -> str:
        """格式化WBS输出."""
        return f"""## WBS工作分解结构

**项目**: {wbs_result.get('project_name', '未知')}

{wbs_result.get('wbs_content', '')}
"""

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        from app.orchestrator.skill_manifest import get_wbs_generation_manifest
        return get_wbs_generation_manifest()


# ==================== 项目情况咨询Skill ====================

class ProjectQuerySkill(BaseSkill):
    """项目情况咨询Skill."""

    skill_name = "project_query"
    display_name = "项目情况咨询"
    description = "回答项目具体情况相关问题。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        question = self.get_param("question")
        project_id = self._get_project_id()

        if not question:
            return self.build_error_result("请提供您的问题")

        # 收集项目数据
        project_data = await self._collect_project_data(project_id)

        # 使用LLM回答
        answer = await self._answer_question(question, project_data)

        return self.build_success_result(
            output={"answer": answer},
            presentation_type="text",
            presentation_data={"text": answer},
        )

    def _get_project_id(self) -> Optional[uuid.UUID]:
        param = self.get_param("project_id")
        if not param:
            return self.project_id
        try:
            return uuid.UUID(param)
        except ValueError:
            return None

    async def _collect_project_data(self, project_id: Optional[uuid.UUID]) -> Dict:
        """收集项目数据."""
        if not project_id or not self._session:
            return {}

        from app.domain.models.project import Project

        result = await self._session.execute(
            select(Project).where(Project.id == project_id),
        )
        project = result.scalar_one_or_none()

        if not project:
            return {}

        return {
            "name": project.name,
            "status": project.status.value if project.status else "未知",
            "progress": project.progress or 0,
        }

    async def _answer_question(self, question: str, project_data: Dict) -> str:
        """回答问题."""
        llm_gateway = get_llm_gateway()

        prompt = f"""作为项目管理助手，请根据以下项目数据回答用户问题。

项目数据：
{project_data}

用户问题：{question}

请直接回答问题：
"""

        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )

        return response.content

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        from app.orchestrator.skill_manifest import get_project_query_manifest
        return get_project_query_manifest()


# ==================== 会议纪要生成Skill ====================

class MeetingMinutesSkill(BaseSkill):
    """会议纪要生成Skill."""

    skill_name = "meeting_minutes"
    display_name = "会议纪要生成"
    description = "根据会议内容生成结构化会议纪要。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        meeting_content = self.get_param("meeting_content")
        meeting_title = self.get_param("meeting_title", "项目会议")
        participants = self.get_param("participants", "")

        if not meeting_content:
            return self.build_error_result("请提供会议内容")

        # 生成会议纪要
        minutes = await self._generate_minutes(
            meeting_content,
            meeting_title,
            participants,
        )

        return self.build_success_result(
            output=minutes,
            presentation_type="text",
            presentation_data={"text": minutes.get("content", "")},
        )

    async def _generate_minutes(
        self,
        content: str,
        title: str,
        participants: str,
    ) -> Dict:
        """生成会议纪要."""
        llm_gateway = get_llm_gateway()

        prompt = f"""请根据以下会议内容生成结构化的会议纪要：

会议标题：{title}
参会人员：{participants}
会议内容：
{content}

请生成包含以下内容的会议纪要：
1. 会议议题
2. 讨论要点
3. 决议事项
4. 待办事项（包括负责人和截止日期）

以Markdown格式输出。
"""

        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        return {
            "content": response.content,
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        from app.orchestrator.skill_manifest import get_meeting_minutes_manifest
        return get_meeting_minutes_manifest()


# ==================== 合规初审Skill ====================

class ComplianceReviewSkill(BaseSkill):
    """预立项/立项材料合规初审Skill."""

    skill_name = "compliance_review"
    display_name = "预立项/立项材料合规初审"
    description = "审核预立项/立项材料的合规性。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        document_id = self.get_param("document_id")
        document_type = self.get_param("document_type", "pre_initiation")

        if not document_id:
            return self.build_error_result("请提供文档ID")

        # 获取文档内容
        document_content = await self._get_document_content(document_id)

        # 执行合规检查
        review_result = await self._review_compliance(
            document_content,
            document_type,
        )

        # 格式化输出
        text = self._format_review_output(review_result)

        return self.build_success_result(
            output=review_result,
            presentation_type="text",
            presentation_data={"text": text},
        )

    async def _get_document_content(self, document_id: str) -> str:
        """获取文档内容."""
        # TODO: 实现从文档系统获取内容
        return "示例文档内容：项目名称、项目背景、项目目标、预算、人员配置等..."

    async def _review_compliance(
        self,
        content: str,
        doc_type: str,
    ) -> Dict:
        """执行合规检查."""
        llm_gateway = get_llm_gateway()

        # 检查清单
        checklist = self._get_checklist(doc_type)

        prompt = f"""请对以下{doc_type}文档进行合规初审：

文档内容：
{content}

检查清单：
{checklist}

请输出：
1. 合规状态（通过/不通过）
2. 各检查项的检查结果
3. 缺失或不合规项
4. 改进建议

以JSON格式输出。
"""

        response = await llm_gateway.generate(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        return {
            "status": "reviewed",
            "result": response.content,
        }

    def _get_checklist(self, doc_type: str) -> str:
        """获取检查清单."""
        checklists = {
            "pre_initiation": """
1. 项目名称是否明确
2. 项目背景是否清晰
3. 项目目标是否可衡量
4. 预估预算是否合理
5. 预估周期是否合理
6. 关键人员是否明确
""",
            "initiation": """
1. 项目章程是否完整
2. 需求文档是否齐全
3. 技术方案是否可行
4. 预算是否详细
5. 里程碑是否明确
6. 风险评估是否完整
""",
        }
        return checklists.get(doc_type, checklists["pre_initiation"])

    def _format_review_output(self, result: Dict) -> str:
        """格式化审查输出."""
        return f"""## 合规初审结果

{result.get('result', '')}
"""

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        from app.orchestrator.skill_manifest import get_compliance_review_manifest
        return get_compliance_review_manifest()


# 导出所有Skill类
__all__ = [
    "WBSGenerationSkill",
    "ProjectQuerySkill",
    "MeetingMinutesSkill",
    "ComplianceReviewSkill",
]