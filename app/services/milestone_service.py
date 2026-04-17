"""
PM Digital Employee - Milestone Service
项目经理数字员工系统 - 里程碑业务服务
"""

import uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, MilestoneNotFoundError, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import MilestoneStatus
from app.domain.models.milestone import Milestone
from app.repositories.milestone_repository import MilestoneRepository
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)


class MilestoneService:
    """
    里程碑业务服务.

    封装里程碑相关的业务逻辑。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化里程碑服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = MilestoneRepository(session)
        self._project_repository = ProjectRepository(session)

    async def create_milestone(
        self,
        project_id: uuid.UUID,
        name: str,
        due_date: date,
        description: Optional[str] = None,
        status: MilestoneStatus = MilestoneStatus.PLANNED,
        is_key_milestone: bool = False,
        sort_order: int = 0,
        user_id: Optional[str] = None,
    ) -> Milestone:
        """
        创建里程碑.

        Args:
            project_id: 项目ID（必填）
            name: 里程碑名称（必填）
            due_date: 计划完成日期（必填）
            description: 里程碑描述
            status: 里程碑状态
            is_key_milestone: 是否关键里程碑
            sort_order: 排序序号
            user_id: 创建用户ID

        Returns:
            Milestone: 创建的里程碑

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 创建里程碑数据（移除created_at/updated_at，Milestone模型中无这些字段）
        milestone_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "name": name,
            "description": description,
            "due_date": due_date,
            "status": status,
            "is_key_milestone": is_key_milestone,
            "sort_order": sort_order,
        }

        milestone = await self._repository.create_in_project(project_id, milestone_data)

        logger.info(
            "Milestone created",
            extra={
                "milestone_id": str(milestone.id),
                "project_id": str(project_id),
                "name": name,
                "due_date": str(due_date),
            }
        )

        return milestone

    async def get_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Milestone:
        """
        获取里程碑信息.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID（用于权限检查）

        Returns:
            Milestone: 里程碑对象

        Raises:
            MilestoneNotFoundError: 里程碑不存在
        """
        milestone = await self._repository.get_by_id_or_error(milestone_id, project_id)
        return milestone

    async def update_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> Milestone:
        """
        更新里程碑.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID（用于权限检查）
            **kwargs: 更新字段

        Returns:
            Milestone: 更新后的里程碑

        Raises:
            MilestoneNotFoundError: 里程碑不存在
        """
        milestone = await self._repository.update_in_project(milestone_id, project_id, kwargs)

        logger.info(
            "Milestone updated",
            extra={
                "milestone_id": str(milestone_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return milestone

    async def achieve_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
        achieved_date: Optional[date] = None,
    ) -> Milestone:
        """
        达成里程碑.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID
            achieved_date: 实际达成日期（默认今天）

        Returns:
            Milestone: 更新后的里程碑
        """
        update_data = {
            "status": MilestoneStatus.ACHIEVED,
            "achieved_date": achieved_date or date.today(),
        }

        return await self.update_milestone(milestone_id, project_id, **update_data)

    async def delay_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
        new_due_date: date,
    ) -> Milestone:
        """
        延期里程碑.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID
            new_due_date: 新的计划完成日期

        Returns:
            Milestone: 更新后的里程碑
        """
        update_data = {
            "status": MilestoneStatus.DELAYED,
            "due_date": new_due_date,
        }

        return await self.update_milestone(milestone_id, project_id, **update_data)

    async def start_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Milestone:
        """
        开始里程碑.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID

        Returns:
            Milestone: 更新后的里程碑
        """
        return await self.update_milestone(
            milestone_id,
            project_id,
            status=MilestoneStatus.IN_PROGRESS,
        )

    async def list_milestones(
        self,
        project_id: uuid.UUID,
        status: Optional[MilestoneStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Milestone]:
        """
        列出里程碑.

        Args:
            project_id: 项目ID
            status: 里程碑状态过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Milestone]: 里程碑列表
        """
        filters = {}
        if status:
            filters["status"] = status

        return await self._repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
            order_by=Milestone.due_date,
        )

    async def get_milestone_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取里程碑统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        return await self._repository.get_statistics(project_id)

    async def get_next_milestone(
        self,
        project_id: uuid.UUID,
    ) -> Optional[Milestone]:
        """
        获取下一个未达成的里程碑.

        Args:
            project_id: 项目ID

        Returns:
            Optional[Milestone]: 下一个里程碑或None
        """
        return await self._repository.get_next_milestone(project_id)

    async def delete_milestone(
        self,
        milestone_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除里程碑.

        Args:
            milestone_id: 里程碑ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        return await self._repository.delete_in_project(milestone_id, project_id)