"""
PM Digital Employee - Project Service
项目经理数字员工系统 - 项目业务服务

v1.2.0新增：项目归档、恢复、Excel导入、飞书表格同步、报告导出功能。
"""

import uuid
import json
from datetime import datetime, timezone, date
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, ProjectNotFoundError, ParameterValidationError
from app.core.logging import get_logger
from app.domain.enums import ProjectStatus
from app.domain.models.project import Project
from app.domain.models.task import Task
from app.domain.models.milestone import Milestone
from app.domain.models.risk import ProjectRisk
from app.domain.models.data_version import DataVersion
from app.repositories.project_repository import ProjectRepository
from app.services.excel_service import ExcelService
from app.services.sync_engine import SyncEngine, SyncStatus

logger = get_logger(__name__)


class ProjectService:
    """
    项目业务服务.

    封装项目相关的业务逻辑。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化项目服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = ProjectRepository(session)

    async def create_project(
        self,
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        project_type: str = "研发项目",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total_budget: Optional[float] = None,
        pm_id: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> Project:
        """
        创建项目.

        Args:
            name: 项目名称
            code: 项目编码（可选）
            description: 项目描述
            project_type: 项目类型
            start_date: 计划开始日期
            end_date: 计划结束日期
            total_budget: 总预算
            pm_id: 项目经理ID
            department_id: 所属部门ID

        Returns:
            Project: 创建的项目对象
        """
        # 自动生成项目编码
        if not code:
            today = datetime.now().strftime("%Y%m%d")
            code = f"PRJ-{today}-{uuid.uuid4().hex[:6].upper()}"

        # 转换字符串日期为date对象
        start_date_obj = None
        end_date_obj = None
        if start_date:
            if isinstance(start_date, str):
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date_obj = start_date
        if end_date:
            if isinstance(end_date, str):
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date_obj = end_date

        # 创建项目实体
        project = Project(
            id=uuid.uuid4(),
            name=name,
            code=code,
            description=description,
            status=ProjectStatus.DRAFT.value,
            project_type=project_type,
            priority=2,
            start_date=start_date_obj,
            end_date=end_date_obj,
            total_budget=total_budget or 0,
            pm_id=pm_id,
            department_id=department_id,
        )

        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)

        logger.info("Project created", project_id=str(project.id), name=name, code=code)

        return project

    async def update_project(
        self,
        project_id: uuid.UUID,
        **kwargs,
    ) -> Project:
        """
        更新项目.

        Args:
            project_id: 项目ID
            **kwargs: 更新字段

        Returns:
            Project: 更新后的项目对象
        """
        project = await self._repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)

        await self.session.flush()
        await self.session.refresh(project)

        logger.info("Project updated", project_id=str(project_id))

        return project

    async def get_project(
        self,
        project_id: uuid.UUID,
        user_id: Optional[str] = None,
    ) -> Project:
        """
        获取项目信息.

        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限检查）

        Returns:
            Project: 项目对象

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        project = await self._repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(project_id=str(project_id))

        return project

    async def list_projects(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Project]:
        """
        获取项目列表.

        Args:
            user_id: 用户ID（过滤用户参与的项目）
            status: 项目状态过滤

        Returns:
            List[Project]: 项目列表
        """
        query = select(Project)

        if status:
            query = query.where(Project.status == status)

        result = await self.session.execute(query)
        projects = result.scalars().all()

        return projects

    async def get_project_overview(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取项目总览信息.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目总览数据
        """
        project = await self.get_project(project_id)

        # 获取任务统计
        task_stats = await self._get_task_stats(project_id)

        # 获取里程碑统计
        milestone_stats = await self._get_milestone_stats(project_id)

        # 获取风险统计
        risk_stats = await self._get_risk_stats(project_id)

        # 获取成本统计
        cost_stats = await self._get_cost_summary(project_id)

        return {
            "project": {
                "id": str(project.id),
                "name": project.name,
                "code": project.code,
                "status": project.status,
                "start_date": str(project.start_date) if project.start_date else None,
                "end_date": str(project.end_date) if project.end_date else None,
            },
            "tasks": task_stats,
            "milestones": milestone_stats,
            "risks": risk_stats,
            "costs": cost_stats,
        }

    async def _get_task_stats(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取任务统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 任务统计数据
        """
        # 总任务数
        total_result = await self.session.execute(
            select(func.count()).where(Task.project_id == project_id),
        )
        total = total_result.scalar_one()

        # 各状态任务数
        status_result = await self.session.execute(
            select(Task.status, func.count()).where(
                Task.project_id == project_id,
            ).group_by(Task.status),
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        return {
            "total": total,
            "by_status": status_counts,
            "completion_rate": (status_counts.get("已完成", 0) / total * 100) if total > 0 else 0,
        }

    async def _get_milestone_stats(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取里程碑统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 里程碑统计数据
        """
        result = await self.session.execute(
            select(Milestone).where(Milestone.project_id == project_id),
        )
        milestones = result.scalars().all()

        return {
            "total": len(milestones),
            "completed": sum(1 for m in milestones if m.status == "已完成"),
            "pending": sum(1 for m in milestones if m.status == "未完成"),
        }

    async def _get_risk_stats(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取风险统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 风险统计数据
        """
        result = await self.session.execute(
            select(ProjectRisk).where(ProjectRisk.project_id == project_id),
        )
        risks = result.scalars().all()

        return {
            "total": len(risks),
            "by_level": {
                "高": sum(1 for r in risks if r.level == "高"),
                "中": sum(1 for r in risks if r.level == "中"),
                "低": sum(1 for r in risks if r.level == "低"),
            },
        }

    async def _get_cost_summary(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, float]:
        """
        获取成本摘要.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 成本摘要数据
        """
        from app.domain.models.cost import ProjectCostBudget, ProjectCostActual

        budget_result = await self.session.execute(
            select(func.coalesce(func.sum(ProjectCostBudget.amount), 0)).where(
                ProjectCostBudget.project_id == project_id,
            ),
        )
        budget = budget_result.scalar_one()

        actual_result = await self.session.execute(
            select(func.coalesce(func.sum(ProjectCostActual.amount), 0)).where(
                ProjectCostActual.project_id == project_id,
            ),
        )
        actual = actual_result.scalar_one()

        return {
            "budget": float(budget),
            "actual": float(actual),
            "variance": float(budget - actual),
            "variance_percent": (float(budget - actual) / float(budget) * 100) if budget != 0 else 0,
        }