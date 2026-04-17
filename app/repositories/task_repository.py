"""
PM Digital Employee - Task Repository
项目经理数字员工系统 - 任务数据访问层
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import ProjectScopedRepository
from app.domain.models.task import Task
from app.domain.enums import TaskStatus, TaskPriority
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskRepository(ProjectScopedRepository[Task]):
    """
    任务Repository.

    提供任务数据的CRUD操作，强制project_id过滤。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化任务Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(Task, session)

    async def list_by_status(
        self,
        project_id: uuid.UUID,
        status: TaskStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        查询指定状态的任务列表.

        Args:
            project_id: 项目ID（必填）
            status: 任务状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 任务列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"status": status},
            skip=skip,
            limit=limit,
        )

    async def list_by_assignee(
        self,
        project_id: uuid.UUID,
        assignee_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        查询指定负责人的任务列表.

        Args:
            project_id: 项目ID（必填）
            assignee_id: 负责人飞书用户ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 任务列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"assignee_id": assignee_id},
            skip=skip,
            limit=limit,
        )

    async def list_delayed_tasks(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        查询延期任务列表.

        Args:
            project_id: 项目ID（必填）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 延期任务列表
        """
        from datetime import date

        try:
            query = select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.end_date < date.today(),
                    Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                )
            ).offset(skip).limit(limit).order_by(Task.end_date)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to list delayed tasks", project_id=str(project_id), error=str(exc))
            raise

    async def count_by_status(
        self,
        project_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
    ) -> int:
        """
        统计任务数量.

        Args:
            project_id: 项目ID（必填）
            status: 任务状态过滤

        Returns:
            int: 任务数量
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
        获取任务统计信息.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import case

        try:
            result = await self.session.execute(
                select(
                    func.count(Task.id).label('total'),
                    func.sum(case((Task.status == TaskStatus.COMPLETED, 1), else_=0)).label('completed'),
                    func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label('in_progress'),
                    func.sum(case((Task.status == TaskStatus.PENDING, 1), else_=0)).label('pending'),
                    func.sum(case((Task.status == TaskStatus.DELAYED, 1), else_=0)).label('delayed'),
                    func.sum(case((Task.status == TaskStatus.BLOCKED, 1), else_=0)).label('blocked'),
                    func.avg(Task.progress).label('avg_progress'),
                ).where(Task.project_id == project_id)
            )

            row = result.first()
            if row:
                return {
                    "total": row.total or 0,
                    "completed": row.completed or 0,
                    "in_progress": row.in_progress or 0,
                    "pending": row.pending or 0,
                    "delayed": row.delayed or 0,
                    "blocked": row.blocked or 0,
                    "avg_progress": int(row.avg_progress or 0),
                }
            return {"total": 0, "completed": 0, "in_progress": 0, "pending": 0, "delayed": 0, "blocked": 0, "avg_progress": 0}
        except Exception as exc:
            logger.error("Failed to get task statistics", project_id=str(project_id), error=str(exc))
            raise

    async def generate_task_code(
        self,
        project_id: uuid.UUID,
    ) -> str:
        """
        生成任务编码.

        格式: TASK-NNN（项目内递增）

        Args:
            project_id: 项目ID

        Returns:
            str: 任务编码
        """
        try:
            result = await self.session.execute(
                select(func.count(Task.id)).where(Task.project_id == project_id)
            )
            count = result.scalar() or 0
            seq_num = count + 1
            return f"TASK-{seq_num:03d}"
        except Exception:
            return f"TASK-{uuid.uuid4().hex[:6]}"