"""
PM Digital Employee - Project Repository
项目经理数字员工系统 - 项目数据访问层
"""

import uuid
from typing import Any, Dict, List, Optional, Type
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.domain.models.project import Project
from app.domain.enums import ProjectStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """
    项目Repository.

    提供项目数据的CRUD操作和查询方法。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化项目Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(Project, session)

    async def get_by_code(self, code: str) -> Optional[Project]:
        """
        根据项目编码查询项目.

        Args:
            code: 项目编码

        Returns:
            Optional[Project]: 项目对象或None
        """
        try:
            result = await self.session.execute(
                select(Project).where(Project.code == code)
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Failed to get project by code", code=code, error=str(exc))
            raise

    async def get_by_pm_id(
        self,
        pm_id: str,
        status: Optional[ProjectStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Project]:
        """
        根据项目经理ID查询项目列表.

        Args:
            pm_id: 项目经理飞书用户ID
            status: 项目状态过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Project]: 项目列表
        """
        try:
            query = select(Project).where(Project.pm_id == pm_id)

            if status:
                query = query.where(Project.status == status)

            query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to get projects by pm_id", pm_id=pm_id, error=str(exc))
            raise

    async def count_by_pm_id(
        self,
        pm_id: str,
        status: Optional[ProjectStatus] = None,
    ) -> int:
        """
        统计项目经理的项目数量.

        Args:
            pm_id: 项目经理飞书用户ID
            status: 项目状态过滤

        Returns:
            int: 项目数量
        """
        try:
            query = select(func.count(Project.id)).where(Project.pm_id == pm_id)

            if status:
                query = query.where(Project.status == status)

            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as exc:
            logger.error("Failed to count projects by pm_id", pm_id=pm_id, error=str(exc))
            raise

    async def list_by_status(
        self,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Project]:
        """
        根据状态查询项目列表.

        Args:
            status: 项目状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Project]: 项目列表
        """
        try:
            query = select(Project).where(Project.status == status)
            query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to list projects by status", status=status, error=str(exc))
            raise

    async def generate_project_code(self) -> str:
        """
        自动生成项目编码.

        格式: PRJ-YYYYMMDD-NNN

        Returns:
            str: 项目编码
        """
        from datetime import datetime

        today = datetime.now()
        date_str = today.strftime("%Y%m%d")

        # 查询今天已有的项目数量
        try:
            result = await self.session.execute(
                select(func.count(Project.id)).where(Project.code.like(f"PRJ-{date_str}%"))
            )
            count = result.scalar() or 0
            seq_num = count + 1
            return f"PRJ-{date_str}-{seq_num:03d}"
        except Exception as exc:
            logger.error("Failed to generate project code", error=str(exc))
            # 使用时间戳作为备选
            return f"PRJ-{date_str}-{today.strftime('%H%M%S')}"