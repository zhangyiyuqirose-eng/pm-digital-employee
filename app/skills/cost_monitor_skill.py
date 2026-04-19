"""
PM Digital Employee - Cost Monitor Skill
项目经理数字员工系统 - 成本监控Skill

监控项目成本执行情况，对比预算与实际支出。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_cost_monitor_manifest
from app.skills.base import BaseSkill


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
        return get_cost_monitor_manifest()