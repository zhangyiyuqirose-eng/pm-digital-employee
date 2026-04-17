"""
PM Digital Employee - Task Service
项目经理数字员工系统 - 任务业务服务
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, TaskNotFoundError, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import TaskStatus, TaskPriority
from app.domain.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)


class TaskService:
    """
    任务业务服务.

    封装任务相关的业务逻辑。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化任务服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = TaskRepository(session)
        self._project_repository = ProjectRepository(session)

    async def create_task(
        self,
        project_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        assignee_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.PENDING,
        estimated_hours: Optional[Decimal] = None,
        deliverable: Optional[str] = None,
        parent_task_id: Optional[uuid.UUID] = None,
        user_id: Optional[str] = None,
    ) -> Task:
        """
        创建任务.

        Args:
            project_id: 项目ID（必填）
            name: 任务名称（必填）
            description: 任务描述
            assignee_id: 负责人飞书用户ID
            assignee_name: 负责人姓名
            start_date: 计划开始日期
            end_date: 计划结束日期
            priority: 任务优先级
            status: 任务状态
            estimated_hours: 预估工时
            deliverable: 交付物描述
            parent_task_id: 父任务ID
            user_id: 创建用户ID

        Returns:
            Task: 创建的任务

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 生成任务编码
        code = await self._repository.generate_task_code(project_id)

        # 创建任务数据
        task_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "code": code,
            "name": name,
            "description": description,
            "assignee_id": assignee_id,
            "assignee_name": assignee_name,
            "start_date": start_date,
            "end_date": end_date,
            "priority": priority,
            "status": status,
            "progress": 0,
            "estimated_hours": estimated_hours,
            "deliverable": deliverable,
            "parent_task_id": parent_task_id,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": user_id,
        }

        task = await self._repository.create_in_project(project_id, task_data)

        logger.info(
            "Task created",
            extra={
                "task_id": str(task.id),
                "project_id": str(project_id),
                "name": name,
                "assignee_id": assignee_id,
            }
        )

        return task

    async def get_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Task:
        """
        获取任务信息.

        Args:
            task_id: 任务ID
            project_id: 项目ID（用于权限检查）

        Returns:
            Task: 任务对象

        Raises:
            TaskNotFoundError: 任务不存在
        """
        task = await self._repository.get_by_id_or_error(task_id, project_id)
        return task

    async def update_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> Task:
        """
        更新任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID（用于权限检查）
            **kwargs: 更新字段

        Returns:
            Task: 更新后的任务

        Raises:
            TaskNotFoundError: 任务不存在
        """
        task = await self._repository.update_in_project(task_id, project_id, kwargs)

        logger.info(
            "Task updated",
            extra={
                "task_id": str(task_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return task

    async def update_task_progress(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        progress: int,
        status: Optional[TaskStatus] = None,
    ) -> Task:
        """
        更新任务进度.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            progress: 进度值（0-100）
            status: 任务状态（可选）

        Returns:
            Task: 更新后的任务
        """
        update_data = {"progress": progress}

        # 根据进度自动更新状态
        if status:
            update_data["status"] = status
        elif progress == 100:
            update_data["status"] = TaskStatus.COMPLETED
            update_data["actual_end_date"] = date.today()
        elif progress > 0:
            update_data["status"] = TaskStatus.IN_PROGRESS
            if "actual_start_date" not in update_data:
                update_data["actual_start_date"] = date.today()

        return await self.update_task(task_id, project_id, **update_data)

    async def complete_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        actual_hours: Optional[Decimal] = None,
    ) -> Task:
        """
        完成任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            actual_hours: 实际工时

        Returns:
            Task: 更新后的任务
        """
        update_data = {
            "status": TaskStatus.COMPLETED,
            "progress": 100,
            "actual_end_date": date.today(),
        }

        if actual_hours:
            update_data["actual_hours"] = actual_hours

        return await self.update_task(task_id, project_id, **update_data)

    async def list_tasks(
        self,
        project_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        列出任务.

        Args:
            project_id: 项目ID
            status: 任务状态过滤
            assignee_id: 负责人过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 任务列表
        """
        filters = {}
        if status:
            filters["status"] = status
        if assignee_id:
            filters["assignee_id"] = assignee_id

        return await self._repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
        )

    async def get_task_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取任务统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        return await self._repository.get_statistics(project_id)

    async def delete_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        return await self._repository.delete_in_project(task_id, project_id)