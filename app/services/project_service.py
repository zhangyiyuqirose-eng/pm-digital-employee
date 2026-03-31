"""
PM Digital Employee - Project Service
项目经理数字员工系统 - 项目业务服务
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import ProjectStatus
from app.domain.models.project import Project
from app.domain.models.task import Task
from app.domain.models.milestone import Milestone
from app.domain.models.risk import ProjectRisk
from app.repositories.project_repository import ProjectRepository

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
        project = await self._repository.get_by_id_with_project(project_id, project_id)

        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        return project

    async def get_project_overview(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取项目总览数据.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目总览数据
        """
        project = await self.get_project(project_id)

        # 查询任务统计
        task_stats = await self._get_task_statistics(project_id)

        # 查询里程碑
        milestones = await self._get_milestones(project_id)

        # 查询风险
        risks = await self._get_risks(project_id)

        # 查询成本
        cost_summary = await self._get_cost_summary(project_id)

        return {
            "project_id": str(project.id),
            "project_name": project.name,
            "project_code": project.project_code,
            "status": project.status.value if project.status else "未知",
            "progress": project.progress or 0,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "pm_id": project.pm_id,
            "pm_name": project.pm_name,
            "description": project.description,
            "task_statistics": task_stats,
            "milestones": milestones,
            "risks": risks,
            "cost_summary": cost_summary,
        }

    async def list_projects(
        self,
        user_id: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Project]:
        """
        列出项目.

        Args:
            user_id: 用户ID
            status: 项目状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Project]: 项目列表
        """
        # TODO: 根据用户权限过滤
        return await self._repository.list_by_project(
            project_id=uuid.uuid4(),  # 占位
            skip=skip,
            limit=limit,
        )

    async def create_project(
        self,
        name: str,
        project_code: str,
        pm_id: Optional[str] = None,
        pm_name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        budget: Optional[float] = None,
    ) -> Project:
        """
        创建项目.

        Args:
            name: 项目名称
            project_code: 项目编码
            pm_id: 项目经理ID
            pm_name: 项目经理姓名
            description: 项目描述
            start_date: 开始日期
            end_date: 结束日期
            budget: 预算

        Returns:
            Project: 创建的项目
        """
        project = Project(
            id=uuid.uuid4(),
            name=name,
            project_code=project_code,
            pm_id=pm_id,
            pm_name=pm_name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            status=ProjectStatus.NOT_STARTED,
            progress=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(project)
        await self.session.commit()

        logger.info(
            "Project created",
            project_id=str(project.id),
            name=name,
        )

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
            Project: 更新后的项目
        """
        project = await self.get_project(project_id)

        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.now(timezone.utc)

        await self.session.commit()

        logger.info(
            "Project updated",
            project_id=str(project_id),
            fields=list(kwargs.keys()),
        )

        return project

    async def update_progress(
        self,
        project_id: uuid.UUID,
    ) -> int:
        """
        更新项目进度（基于任务进度计算）.

        Args:
            project_id: 项目ID

        Returns:
            int: 新进度值
        """
        # 查询所有任务
        result = await self.session.execute(
            select(Task).where(Task.project_id == project_id),
        )
        tasks = result.scalars().all()

        if not tasks:
            return 0

        # 计算平均进度
        total_progress = sum(t.progress or 0 for t in tasks)
        avg_progress = int(total_progress / len(tasks))

        # 更新项目进度
        project = await self.get_project(project_id)
        project.progress = avg_progress
        project.updated_at = datetime.now(timezone.utc)

        await self.session.commit()

        return avg_progress

    async def _get_task_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """获取任务统计."""
        result = await self.session.execute(
            select(
                Task.status,
                func.count(Task.id),
            ).where(
                Task.project_id == project_id,
            ).group_by(Task.status),
        )

        stats = {"total": 0}
        for row in result:
            status = row[0].value if row[0] else "unknown"
            count = row[1]
            stats[status] = count
            stats["total"] += count

        return stats

    async def _get_milestones(
        self,
        project_id: uuid.UUID,
    ) -> List[Dict]:
        """获取里程碑列表."""
        result = await self.session.execute(
            select(Milestone).where(
                Milestone.project_id == project_id,
            ).order_by(Milestone.due_date),
        )
        milestones = result.scalars().all()

        return [
            {
                "id": str(m.id),
                "name": m.name,
                "due_date": m.due_date,
                "status": m.status.value if m.status else "pending",
            }
            for m in milestones
        ]

    async def _get_risks(
        self,
        project_id: uuid.UUID,
    ) -> List[Dict]:
        """获取风险列表."""
        result = await self.session.execute(
            select(ProjectRisk).where(
                ProjectRisk.project_id == project_id,
            ),
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

    async def _get_cost_summary(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, float]:
        """获取成本摘要."""
        from app.domain.models.cost import ProjectCostBudget, ProjectCostActual

        # 预算
        budget_result = await self.session.execute(
            select(func.sum(ProjectCostBudget.amount)).where(
                ProjectCostBudget.project_id == project_id,
            ),
        )
        budget = budget_result.scalar() or 0

        # 实际
        actual_result = await self.session.execute(
            select(func.sum(ProjectCostActual.amount)).where(
                ProjectCostActual.project_id == project_id,
            ),
        )
        actual = actual_result.scalar() or 0

        return {
            "budget": float(budget),
            "actual": float(actual),
            "variance": float(budget - actual),
        }