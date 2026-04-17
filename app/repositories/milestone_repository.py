"""
PM Digital Employee - Milestone Repository
项目经理数字员工系统 - 里程碑数据访问层
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import ProjectScopedRepository
from app.domain.models.milestone import Milestone
from app.domain.enums import MilestoneStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class MilestoneRepository(ProjectScopedRepository[Milestone]):
    """
    里程碑Repository.

    提供里程碑数据的CRUD操作，强制project_id过滤。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化里程碑Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(Milestone, session)

    async def list_by_status(
        self,
        project_id: uuid.UUID,
        status: MilestoneStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Milestone]:
        """
        查询指定状态的里程碑列表.

        Args:
            project_id: 项目ID（必填）
            status: 里程碑状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Milestone]: 里程碑列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"status": status},
            skip=skip,
            limit=limit,
            order_by=Milestone.due_date,
        )

    async def list_delayed_milestones(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Milestone]:
        """
        查询延期里程碑列表.

        Args:
            project_id: 项目ID（必填）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Milestone]: 延期里程碑列表
        """
        from datetime import date

        try:
            query = select(Milestone).where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.due_date < date.today(),
                    Milestone.status.notin_([MilestoneStatus.ACHIEVED, MilestoneStatus.CANCELLED]),
                )
            ).offset(skip).limit(limit).order_by(Milestone.due_date)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to list delayed milestones", project_id=str(project_id), error=str(exc))
            raise

    async def list_key_milestones(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Milestone]:
        """
        查询关键里程碑列表.

        Args:
            project_id: 项目ID（必填）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Milestone]: 关键里程碑列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"is_key_milestone": True},
            skip=skip,
            limit=limit,
            order_by=Milestone.due_date,
        )

    async def get_next_milestone(
        self,
        project_id: uuid.UUID,
    ) -> Optional[Milestone]:
        """
        获取下一个未达成的里程碑.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Optional[Milestone]: 下一个里程碑或None
        """
        from datetime import date

        try:
            query = select(Milestone).where(
                and_(
                    Milestone.project_id == project_id,
                    Milestone.status == MilestoneStatus.PLANNED,
                    Milestone.due_date >= date.today(),
                )
            ).order_by(Milestone.due_date).limit(1)

            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Failed to get next milestone", project_id=str(project_id), error=str(exc))
            raise

    async def count_by_status(
        self,
        project_id: uuid.UUID,
        status: Optional[MilestoneStatus] = None,
    ) -> int:
        """
        统计里程碑数量.

        Args:
            project_id: 项目ID（必填）
            status: 里程碑状态过滤

        Returns:
            int: 里程碑数量
        """
        filters = {}
        if status:
            filters["status"] = status

        return await self.count_by_project(project_id=project_id, filters=filters)

    async def get_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取里程碑统计信息.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import case

        try:
            result = await self.session.execute(
                select(
                    func.count(Milestone.id).label('total'),
                    func.sum(case((Milestone.status == MilestoneStatus.ACHIEVED, 1), else_=0)).label('achieved'),
                    func.sum(case((Milestone.status == MilestoneStatus.PLANNED, 1), else_=0)).label('planned'),
                    func.sum(case((Milestone.status == MilestoneStatus.IN_PROGRESS, 1), else_=0)).label('in_progress'),
                    func.sum(case((Milestone.status == MilestoneStatus.DELAYED, 1), else_=0)).label('delayed'),
                    func.sum(case((Milestone.is_key_milestone == True, 1), else_=0)).label('key_milestones'),
                ).where(Milestone.project_id == project_id)
            )

            row = result.first()
            if row:
                return {
                    "total": row.total or 0,
                    "achieved": row.achieved or 0,
                    "planned": row.planned or 0,
                    "in_progress": row.in_progress or 0,
                    "delayed": row.delayed or 0,
                    "key_milestones": row.key_milestones or 0,
                }
            return {"total": 0, "achieved": 0, "planned": 0, "in_progress": 0, "delayed": 0, "key_milestones": 0}
        except Exception as exc:
            logger.error("Failed to get milestone statistics", project_id=str(project_id), error=str(exc))
            raise