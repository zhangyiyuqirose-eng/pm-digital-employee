"""
PM Digital Employee - Project Overview Skill
项目经理数字员工系统 - 项目总览查询Skill

查询项目的整体状态信息，包括进度、里程碑、风险、成本等。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import SkillExecutionError
from app.domain.models.project import Project
from app.domain.models.task import Task
from app.domain.models.milestone import Milestone
from app.domain.models.risk import ProjectRisk
from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_project_overview_manifest
from app.skills.base import BaseSkill


class ProjectOverviewSkill(BaseSkill):
    """
    项目总览查询Skill.

    查询项目的整体状态信息。
    """

    skill_name = "project_overview"
    display_name = "项目总览查询"
    description = "查询项目的整体状态信息，包括进度、里程碑、风险、成本等。用户可以输入'查看项目状态'、'项目总览'、'项目概况'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """
        执行Skill.

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 获取项目ID参数
        project_id = self._get_project_id()

        if not project_id:
            return self.build_error_result("请提供项目ID或项目名称")

        # 查询项目信息
        project_data = await self._query_project_data(project_id)

        if not project_data:
            return self.build_error_result(f"未找到项目: {project_id}")

        # 构建展示数据
        presentation_data = self._build_presentation_data(project_data)

        return self.build_success_result(
            output=project_data,
            presentation_type="card",
            presentation_data=presentation_data,
        )

    def _get_project_id(self) -> Optional[uuid.UUID]:
        """
        获取项目ID.

        Returns:
            Optional[uuid.UUID]: 项目ID
        """
        # 从参数获取
        param = self.get_param("project_id")

        if not param:
            # 从上下文获取
            return self.project_id

        # 尝试解析UUID
        try:
            return uuid.UUID(param)
        except ValueError:
            # 可能是项目名称，需要查询
            # TODO: 根据名称查询项目ID
            return None

    async def _query_project_data(
        self,
        project_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        查询项目数据.

        Args:
            project_id: 项目ID

        Returns:
            Optional[Dict]: 项目数据
        """
        if not self._session:
            # 返回模拟数据
            return self._get_mock_data(project_id)

        try:
            # 查询项目基本信息
            result = await self._session.execute(
                select(Project).where(Project.id == project_id),
            )
            project = result.scalar_one_or_none()

            if not project:
                return None

            # 查询任务
            tasks = await self._query_tasks(project_id)

            # 查询里程碑
            milestones = await self._query_milestones(project_id)

            # 查询风险
            risks = await self._query_risks(project_id)

            # 查询成本
            cost_summary = await self._query_cost_summary(project_id)

            # 计算进度
            progress = self._calculate_progress(tasks)

            return {
                "project_id": str(project.id),
                "project_name": project.name,
                "project_code": project.project_code,
                "status": project.status.value if project.status else "未知",
                "progress": progress,
                "start_date": str(project.start_date) if project.start_date else "",
                "end_date": str(project.end_date) if project.end_date else "",
                "pm_name": project.pm_name or "未知",
                "tasks": {
                    "total": len(tasks),
                    "completed": len([t for t in tasks if t.get("status") == "completed"]),
                    "in_progress": len([t for t in tasks if t.get("status") == "in_progress"]),
                },
                "milestones": milestones,
                "risks": risks,
                "cost_summary": cost_summary,
            }

        except Exception as e:
            raise SkillExecutionError(
                skill_name=self.skill_name,
                message=f"查询项目数据失败: {str(e)}",
            )

    async def _query_tasks(
        self,
        project_id: uuid.UUID,
    ) -> list:
        """查询任务列表."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(Task).where(Task.project_id == project_id),
        )
        tasks = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "name": t.name,
                "status": t.status.value if t.status else "pending",
                "progress": t.progress or 0,
            }
            for t in tasks
        ]

    async def _query_milestones(
        self,
        project_id: uuid.UUID,
    ) -> list:
        """查询里程碑列表."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(Milestone).where(Milestone.project_id == project_id),
        )
        milestones = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "name": m.name,
                "due_date": str(m.due_date) if m.due_date else "",
                "status": m.status.value if m.status else "pending",
            }
            for m in milestones
        ]

    async def _query_risks(
        self,
        project_id: uuid.UUID,
    ) -> list:
        """查询风险列表."""
        if not self._session:
            return []

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

    async def _query_cost_summary(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """查询成本摘要."""
        if not self._session:
            return {"budget": 0, "actual": 0, "variance": 0}

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

        variance = total_budget - total_actual

        return {
            "budget": float(total_budget),
            "actual": float(total_actual),
            "variance": float(variance),
            "variance_percent": (variance / total_budget * 100) if total_budget > 0 else 0,
        }

    def _calculate_progress(
        self,
        tasks: list,
    ) -> int:
        """计算整体进度."""
        if not tasks:
            return 0

        total_progress = sum(t.get("progress", 0) for t in tasks)
        return int(total_progress / len(tasks))

    def _build_presentation_data(
        self,
        project_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        构建展示数据.

        Args:
            project_data: 项目数据

        Returns:
            Dict: 展示数据
        """
        return {
            "title": f"项目总览：{project_data.get('project_name', '未知项目')}",
            "template": "blue",
            "fields": {
                "项目状态": project_data.get("status", "未知"),
                "整体进度": f"{project_data.get('progress', 0)}%",
                "项目经理": project_data.get("pm_name", "未知"),
                "起止日期": f"{project_data.get('start_date', '')} - {project_data.get('end_date', '')}",
            },
            "milestones": project_data.get("milestones", []),
            "risks": project_data.get("risks", []),
            "cost_summary": project_data.get("cost_summary", {}),
        }

    def _get_mock_data(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """获取模拟数据."""
        return {
            "project_id": str(project_id),
            "project_name": "示例项目",
            "project_code": "PRJ-2024-001",
            "status": "进行中",
            "progress": 65,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "pm_name": "张三",
            "tasks": {
                "total": 20,
                "completed": 12,
                "in_progress": 5,
            },
            "milestones": [
                {"name": "需求评审", "due_date": "2024-03-01", "status": "completed"},
                {"name": "设计完成", "due_date": "2024-06-01", "status": "completed"},
                {"name": "开发完成", "due_date": "2024-09-01", "status": "in_progress"},
                {"name": "测试完成", "due_date": "2024-11-01", "status": "pending"},
            ],
            "risks": [
                {"description": "技术方案存在不确定性", "level": "medium"},
                {"description": "人员流动风险", "level": "low"},
            ],
            "cost_summary": {
                "budget": 1000000,
                "actual": 650000,
                "variance": 350000,
                "variance_percent": 35,
            },
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        return get_project_overview_manifest()