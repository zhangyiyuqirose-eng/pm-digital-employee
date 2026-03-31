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


class TaskUpdateSkill(BaseSkill):
    """
    任务进度更新Skill.

    更新任务进度状态。
    """

    skill_name = "task_update"
    display_name = "任务进度更新"
    description = "更新任务进度状态，包括完成百分比、状态变更、备注添加。用户可以输入'更新任务进度'、'完成任务'、'任务状态'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        # 获取参数
        task_id = self.get_param("task_id")
        progress = self.get_param("progress")
        status = self.get_param("status")
        notes = self.get_param("notes", "")

        if not task_id:
            return self.build_error_result("请提供任务ID或任务名称")

        # 验证进度值
        if progress is not None:
            try:
                progress = int(progress)
                if progress < 0 or progress > 100:
                    return self.build_error_result("进度值应在0-100之间")
            except ValueError:
                return self.build_error_result("进度值应为数字")

        # 验证状态值
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        if status and status not in valid_statuses:
            return self.build_error_result(f"状态值应为: {', '.join(valid_statuses)}")

        # 更新任务
        result = await self._update_task(task_id, progress, status, notes)

        return self.build_success_result(
            output=result,
            presentation_type="text",
            presentation_data={
                "text": f"✅ 任务 **{result.get('task_name', task_id)}** 已更新\n\n"
                f"- 进度: {result.get('progress', 0)}%\n"
                f"- 状态: {result.get('status', '未知')}\n"
                f"- 备注: {result.get('notes', '无')}",
            },
        )

    async def _update_task(
        self,
        task_id: str,
        progress: Optional[int],
        status: Optional[str],
        notes: str,
    ) -> Dict[str, Any]:
        """
        更新任务.

        Args:
            task_id: 任务ID
            progress: 进度
            status: 状态
            notes: 备注

        Returns:
            Dict: 更新结果
        """
        if not self._session:
            # 返回模拟结果
            return {
                "task_id": task_id,
                "task_name": f"任务_{task_id}",
                "progress": progress or 0,
                "status": status or "in_progress",
                "notes": notes,
            }

        from app.domain.models.task import Task

        # 尝试解析UUID
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            # 可能是任务名称，需要查询
            result = await self._session.execute(
                select(Task).where(Task.name == task_id),
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError(f"未找到任务: {task_id}")

            task_uuid = task.id

        # 查询任务
        result = await self._session.execute(
            select(Task).where(Task.id == task_uuid),
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 更新字段
        if progress is not None:
            task.progress = progress

        if status:
            task.status = status

        if notes:
            task.notes = notes

        await self._session.commit()

        return {
            "task_id": str(task.id),
            "task_name": task.name,
            "progress": task.progress or 0,
            "status": task.status.value if task.status else "unknown",
            "notes": task.notes or "",
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_task_update_manifest
        return get_task_update_manifest()


class RiskAlertSkill(BaseSkill):
    """
    风险识别与预警Skill.

    识别项目风险并发出预警。
    """

    skill_name = "risk_alert"
    display_name = "风险识别与预警"
    description = "识别项目风险并发出预警，分析风险等级、影响范围、应对措施。用户可以输入'查看风险'、'风险预警'、'项目风险'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        project_id = self._get_project_id()

        if not project_id:
            return self.build_error_result("请提供项目ID")

        # 查询风险
        risks = await self._query_risks(project_id)

        # 分类风险
        high_risks = [r for r in risks if r.get("level") == "high"]
        medium_risks = [r for r in risks if r.get("level") == "medium"]
        low_risks = [r for r in risks if r.get("level") == "low"]

        # 构建展示数据
        text = f"## 风险预警\n\n"
        text += f"共识别风险 {len(risks)} 项\n\n"

        if high_risks:
            text += "### 🔴 高风险\n"
            for r in high_risks:
                text += f"- {r.get('description', '')}\n"
            text += "\n"

        if medium_risks:
            text += "### 🟡 中风险\n"
            for r in medium_risks:
                text += f"- {r.get('description', '')}\n"
            text += "\n"

        if low_risks:
            text += f"### 🟢 低风险\n共 {len(low_risks)} 项\n\n"

        if not risks:
            text += "✅ 当前无风险项\n"

        return self.build_success_result(
            output={
                "risks": risks,
                "high_risk_count": len(high_risks),
                "medium_risk_count": len(medium_risks),
                "low_risk_count": len(low_risks),
            },
            presentation_type="text",
            presentation_data={"text": text},
        )

    def _get_project_id(self) -> Optional[uuid.UUID]:
        """获取项目ID."""
        param = self.get_param("project_id")
        if not param:
            return self.project_id
        try:
            return uuid.UUID(param)
        except ValueError:
            return None

    async def _query_risks(self, project_id: uuid.UUID) -> list:
        """查询风险."""
        if not self._session:
            return [
                {"description": "技术方案存在不确定性", "level": "medium"},
                {"description": "关键人员可能离职", "level": "high"},
                {"description": "第三方依赖更新风险", "level": "low"},
            ]

        from app.domain.models.risk import ProjectRisk

        result = await self._session.execute(
            select(ProjectRisk).where(ProjectRisk.project_id == project_id),
        )
        risks = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "description": r.description,
                "level": r.level.value if r.level else "low",
                "status": r.status.value if r.status else "open",
            }
            for r in risks
        ]

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_risk_alert_manifest
        return get_risk_alert_manifest()


class CostMonitorSkill(BaseSkill):
    """
    成本监控Skill.

    监控项目成本执行情况。
    """

    skill_name = "cost_monitor"
    display_name = "成本监控"
    description = "监控项目成本执行情况，对比预算与实际支出，预警超支风险。用户可以输入'查看成本'、'成本监控'、'预算情况'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        project_id = self._get_project_id()

        if not project_id:
            return self.build_error_result("请提供项目ID")

        # 查询成本数据
        cost_data = await self._query_cost_data(project_id)

        # 构建展示数据
        text = "## 成本监控\n\n"
        text += f"- **预算总额**: ¥{cost_data.get('budget', 0):,.0f}\n"
        text += f"- **实际支出**: ¥{cost_data.get('actual', 0):,.0f}\n"
        text += f"- **偏差**: ¥{cost_data.get('variance', 0):,.0f}\n"
        text += f"- **偏差率**: {cost_data.get('variance_percent', 0):.1f}%\n"

        # 预警
        variance_percent = cost_data.get('variance_percent', 0)
        if variance_percent < -10:
            text += "\n⚠️ **预警**: 支出超过预算10%以上，请注意控制成本"
        elif variance_percent < 0:
            text += "\nℹ️ **提示**: 支出已超过预算，请关注成本"
        else:
            text += "\n✅ **状态**: 成本控制良好"

        return self.build_success_result(
            output=cost_data,
            presentation_type="text",
            presentation_data={"text": text},
        )

    def _get_project_id(self) -> Optional[uuid.UUID]:
        """获取项目ID."""
        param = self.get_param("project_id")
        if not param:
            return self.project_id
        try:
            return uuid.UUID(param)
        except ValueError:
            return None

    async def _query_cost_data(self, project_id: uuid.UUID) -> Dict[str, Any]:
        """查询成本数据."""
        if not self._session:
            return {
                "budget": 1000000,
                "actual": 650000,
                "variance": 350000,
                "variance_percent": 35,
            }

        from app.domain.models.cost import ProjectCostBudget, ProjectCostActual

        # 查询预算
        budget_result = await self._session.execute(
            select(ProjectCostBudget).where(
                ProjectCostBudget.project_id == project_id,
            ),
        )
        budgets = budget_result.scalars().all()
        total_budget = sum(b.amount or 0 for b in budgets)

        # 查询实际支出
        actual_result = await self._session.execute(
            select(ProjectCostActual).where(
                ProjectCostActual.project_id == project_id,
            ),
        )
        actuals = actual_result.scalars().all()
        total_actual = sum(a.amount or 0 for a in actuals)

        variance = float(total_budget - total_actual)
        variance_percent = (variance / float(total_budget) * 100) if total_budget > 0 else 0

        return {
            "budget": float(total_budget),
            "actual": float(total_actual),
            "variance": variance,
            "variance_percent": variance_percent,
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import get_cost_monitor_manifest
        return get_cost_monitor_manifest()