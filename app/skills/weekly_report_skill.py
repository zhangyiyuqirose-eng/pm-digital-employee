"""
PM Digital Employee - Weekly Report Skill
项目经理数字员工系统 - 项目周报生成Skill

自动生成项目周报，汇总本周任务进展、下周计划、风险状态等。
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_gateway import get_llm_gateway
from app.ai.prompt_manager import get_prompt_manager
from app.core.config import settings
from app.core.exceptions import SkillExecutionError
from app.domain.models.project import Project
from app.domain.models.task import Task
from app.domain.models.risk import ProjectRisk
from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_weekly_report_manifest
from app.skills.base import BaseSkill


class WeeklyReportSkill(BaseSkill):
    """
    项目周报生成Skill.

    自动生成项目周报。
    """

    skill_name = "weekly_report"
    display_name = "项目周报生成"
    description = "自动生成项目周报，汇总本周任务进展、下周计划、风险状态等。用户可以输入'生成周报'、'本周周报'、'写周报'等触发。"
    version = "1.0.0"

    def __init__(
        self,
        manifest: Optional[SkillManifest] = None,
        context: Optional[SkillExecutionContext] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """初始化."""
        super().__init__(manifest, context, session)
        self._llm_gateway = get_llm_gateway()
        self._prompt_manager = get_prompt_manager()

    async def execute(self) -> SkillExecutionResult:
        """
        执行Skill.

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 获取项目ID
        project_id = self._get_project_id()

        if not project_id:
            return self.build_error_result("请提供项目ID")

        # 确定周范围
        week_start, week_end = self._get_week_range()

        # 收集周报数据
        report_data = await self._collect_report_data(project_id, week_start, week_end)

        # 生成周报内容
        report_content = await self._generate_report_content(report_data)

        return self.build_success_result(
            output={
                "report_content": report_content,
                "week_start": str(week_start.date()),
                "week_end": str(week_end.date()),
            },
            presentation_type="text",
            presentation_data={"text": report_content},
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

    def _get_week_range(self) -> tuple:
        """
        获取周范围.

        Returns:
            tuple: (开始时间, 结束时间)
        """
        week_start_param = self.get_param("week_start")

        if week_start_param == "上周":
            # 上周一到上周日
            today = datetime.now(timezone.utc).date()
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            return (
                datetime.combine(last_monday, datetime.min.time()).replace(tzinfo=timezone.utc),
                datetime.combine(last_sunday, datetime.max.time()).replace(tzinfo=timezone.utc),
            )
        elif week_start_param == "本周" or not week_start_param:
            # 本周一到今天
            today = datetime.now(timezone.utc).date()
            this_monday = today - timedelta(days=today.weekday())
            return (
                datetime.combine(this_monday, datetime.min.time()).replace(tzinfo=timezone.utc),
                datetime.now(timezone.utc),
            )
        else:
            # 尝试解析日期
            try:
                start_date = datetime.strptime(week_start_param, "%Y-%m-%d")
                end_date = start_date + timedelta(days=6)
                return (
                    start_date.replace(tzinfo=timezone.utc),
                    end_date.replace(tzinfo=timezone.utc),
                )
            except ValueError:
                return self._get_week_range()  # 默认本周

    async def _collect_report_data(
        self,
        project_id: uuid.UUID,
        week_start: datetime,
        week_end: datetime,
    ) -> Dict[str, Any]:
        """
        收集周报数据.

        Args:
            project_id: 项目ID
            week_start: 周开始时间
            week_end: 周结束时间

        Returns:
            Dict: 周报数据
        """
        if not self._session:
            return self._get_mock_report_data(week_start, week_end)

        try:
            # 查询项目信息
            project_result = await self._session.execute(
                select(Project).where(Project.id == project_id),
            )
            project = project_result.scalar_one_or_none()

            if not project:
                raise SkillExecutionError(
                    skill_name=self.skill_name,
                    message=f"项目不存在: {project_id}",
                )

            # 查询本周完成的任务
            completed_tasks = await self._query_completed_tasks(
                project_id, week_start, week_end,
            )

            # 查询进行中任务
            in_progress_tasks = await self._query_in_progress_tasks(project_id)

            # 查询风险
            risks = await self._query_risks(project_id)

            return {
                "project_name": project.name,
                "project_status": project.status.value if project.status else "未知",
                "progress": project.progress or 0,
                "week_start": str(week_start.date()),
                "week_end": str(week_end.date()),
                "tasks_completed": completed_tasks,
                "tasks_in_progress": in_progress_tasks,
                "risks": risks,
                "next_week_plan": [],  # TODO: 从计划获取
            }

        except Exception as e:
            raise SkillExecutionError(
                skill_name=self.skill_name,
                message=f"收集周报数据失败: {str(e)}",
            )

    async def _query_completed_tasks(
        self,
        project_id: uuid.UUID,
        week_start: datetime,
        week_end: datetime,
    ) -> List[Dict]:
        """查询本周完成的任务."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.status == "completed",
                    Task.updated_at >= week_start,
                    Task.updated_at <= week_end,
                ),
            ),
        )
        tasks = result.scalars().all()

        return [
            {"name": t.name, "progress": t.progress or 100}
            for t in tasks
        ]

    async def _query_in_progress_tasks(
        self,
        project_id: uuid.UUID,
    ) -> List[Dict]:
        """查询进行中任务."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.status == "in_progress",
                ),
            ),
        )
        tasks = result.scalars().all()

        return [
            {"name": t.name, "progress": t.progress or 0}
            for t in tasks
        ]

    async def _query_risks(
        self,
        project_id: uuid.UUID,
    ) -> List[Dict]:
        """查询风险."""
        if not self._session:
            return []

        result = await self._session.execute(
            select(ProjectRisk).where(
                ProjectRisk.project_id == project_id,
            ),
        )
        risks = result.scalars().all()

        return [
            {"description": r.description, "level": r.level.value if r.level else "low"}
            for r in risks
        ]

    async def _generate_report_content(
        self,
        report_data: Dict[str, Any],
    ) -> str:
        """
        生成周报内容.

        Args:
            report_data: 周报数据

        Returns:
            str: 周报内容
        """
        try:
            # 使用Prompt模板
            prompt = self._prompt_manager.render(
                "weekly_report",
                **report_data,
            )

            response = await self._llm_gateway.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7,
            )

            return response.content

        except Exception as e:
            # 回退到模板生成
            return self._generate_template_report(report_data)

    def _generate_template_report(
        self,
        data: Dict[str, Any],
    ) -> str:
        """生成模板周报."""
        report = f"""# 项目周报

## 基本信息
- 项目名称：{data.get('project_name', '未知')}
- 报告周期：{data.get('week_start', '')} 至 {data.get('week_end', '')}
- 项目状态：{data.get('project_status', '未知')}
- 整体进度：{data.get('progress', 0)}%

## 本周工作完成情况
"""
        for task in data.get("tasks_completed", []):
            report += f"- ✅ {task.get('name', '')}\n"

        report += "\n## 进行中任务\n"
        for task in data.get("tasks_in_progress", []):
            report += f"- ⏳ {task.get('name', '')} ({task.get('progress', 0)}%)\n"

        report += "\n## 风险提示\n"
        risks = data.get("risks", [])
        if risks:
            for risk in risks:
                level_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    risk.get("level", "low"), "⚪"
                )
                report += f"- {level_icon} {risk.get('description', '')}\n"
        else:
            report += "- 无风险\n"

        report += "\n## 下周计划\n"
        for plan in data.get("next_week_plan", []):
            report += f"- {plan}\n"

        if not data.get("next_week_plan"):
            report += "- 待规划\n"

        return report

    def _get_mock_report_data(
        self,
        week_start: datetime,
        week_end: datetime,
    ) -> Dict[str, Any]:
        """获取模拟周报数据."""
        return {
            "project_name": "示例项目",
            "project_status": "进行中",
            "progress": 65,
            "week_start": str(week_start.date()),
            "week_end": str(week_end.date()),
            "tasks_completed": [
                {"name": "完成用户模块开发", "progress": 100},
                {"name": "完成API文档编写", "progress": 100},
            ],
            "tasks_in_progress": [
                {"name": "订单模块开发", "progress": 60},
                {"name": "性能优化", "progress": 30},
            ],
            "risks": [
                {"description": "第三方接口稳定性问题", "level": "medium"},
            ],
            "next_week_plan": [
                "完成订单模块开发",
                "开始集成测试",
                "准备演示环境",
            ],
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        return get_weekly_report_manifest()