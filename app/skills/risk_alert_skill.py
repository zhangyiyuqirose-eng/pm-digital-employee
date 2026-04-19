"""
PM Digital Employee - Risk Alert Skill
项目经理数字员工系统 - 风险识别与预警Skill

识别项目风险并发出预警。
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_risk_alert_manifest
from app.skills.base import BaseSkill


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

    async def _query_risks(self, project_id: uuid.UUID) -> List[Dict[str, Any]]:
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
        return get_risk_alert_manifest()