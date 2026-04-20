"""
PM Digital Employee - Meeting Minutes Repository
项目经理数字员工系统 - 会议纪要数据仓库

提供会议纪要数据的CRUD操作，遵循项目级数据隔离原则。
"""

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DataNotFoundError
from app.core.logging import get_logger
from app.domain.enums import DataSource, MeetingStatus
from app.domain.models.meeting_minutes import MeetingMinutes
from app.repositories.base import ProjectScopedRepository

logger = get_logger(__name__)


class MeetingMinutesRepository(ProjectScopedRepository[MeetingMinutes]):
    """
    会议纪要数据仓库.

    继承ProjectScopedRepository，强制project_id过滤。
    提供会议纪要的CRUD操作和查询功能。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化会议纪要数据仓库.

        Args:
            session: 数据库会话
        """
        super().__init__(MeetingMinutes, session)

    async def generate_meeting_code(self, project_id: uuid.UUID) -> str:
        """
        生成会议编码.

        格式：MM-YYYYMMDD-NNN（MM为会议纪要缩写）

        Args:
            project_id: 项目ID

        Returns:
            str: 会议编码
        """
        today = date.today()
        date_str = today.strftime("%Y%m%d")

        # 查询当天已有会议纪要数量
        result = await self.session.execute(
            select(func.count(MeetingMinutes.id))
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.meeting_code.like(f"MM-{date_str}%")
                )
            )
        )
        count = result.scalar() or 0

        # 生成编码
        code = f"MM-{date_str}-{count + 1:03d}"
        return code

    async def get_current_minutes(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MeetingMinutes]:
        """
        获取项目当前版本会议纪要列表.

        Args:
            project_id: 项目ID
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            List[MeetingMinutes]: 会议纪要列表
        """
        result = await self.session.execute(
            select(MeetingMinutes)
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.is_current == True,
                )
            )
            .order_by(desc(MeetingMinutes.meeting_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        project_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> List[MeetingMinutes]:
        """
        获取指定日期范围内的会议纪要.

        Args:
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[MeetingMinutes]: 会议纪要列表
        """
        result = await self.session.execute(
            select(MeetingMinutes)
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.meeting_date >= start_date,
                    MeetingMinutes.meeting_date <= end_date,
                    MeetingMinutes.is_current == True,
                )
            )
            .order_by(desc(MeetingMinutes.meeting_date))
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        project_id: uuid.UUID,
        status: MeetingStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MeetingMinutes]:
        """
        获取指定状态的会议纪要列表.

        Args:
            project_id: 项目ID
            status: 会议纪要状态
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            List[MeetingMinutes]: 会议纪要列表
        """
        result = await self.session.execute(
            select(MeetingMinutes)
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.status == status,
                    MeetingMinutes.is_current == True,
                )
            )
            .order_by(desc(MeetingMinutes.meeting_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_external_id(
        self,
        external_id: str,
    ) -> Optional[MeetingMinutes]:
        """
        根据外部系统ID查询会议纪要.

        Args:
            external_id: 外部系统ID（飞书表格行ID等）

        Returns:
            Optional[MeetingMinutes]: 会议纪要对象或None
        """
        result = await self.session.execute(
            select(MeetingMinutes)
            .where(MeetingMinutes.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def update_sync_info(
        self,
        minutes_id: uuid.UUID,
        sync_version: int,
        external_id: Optional[str] = None,
    ) -> MeetingMinutes:
        """
        更新同步信息.

        Args:
            minutes_id: 会议纪要ID
            sync_version: 同步版本号
            external_id: 外部系统ID

        Returns:
            MeetingMinutes: 更新后的会议纪要

        Raises:
            DataNotFoundError: 会议纪要不存在
        """
        minutes = await self.get_by_id(minutes_id)
        if minutes is None:
            raise DataNotFoundError(f"会议纪要不存在: {minutes_id}")

        minutes.sync_version = sync_version
        minutes.last_sync_at = datetime.now(timezone.utc)
        if external_id:
            minutes.external_id = external_id

        await self.session.flush()
        return minutes

    async def mark_as_history(
        self,
        minutes_id: uuid.UUID,
    ) -> None:
        """
        将会议纪要标记为历史版本.

        Args:
            minutes_id: 会议纪要ID
        """
        result = await self.session.execute(
            select(MeetingMinutes).where(MeetingMinutes.id == minutes_id)
        )
        minutes = result.scalar_one_or_none()

        if minutes:
            minutes.is_current = False
            await self.session.flush()

    async def count_by_project(
        self,
        project_id: uuid.UUID,
    ) -> int:
        """
        统计项目会议纪要数量.

        Args:
            project_id: 项目ID

        Returns:
            int: 会议纪要数量
        """
        result = await self.session.execute(
            select(func.count(MeetingMinutes.id))
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.is_current == True,
                )
            )
        )
        return result.scalar() or 0

    async def search_by_title(
        self,
        project_id: uuid.UUID,
        keyword: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MeetingMinutes]:
        """
        按标题搜索会议纪要.

        Args:
            project_id: 项目ID
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            List[MeetingMinutes]: 会议纪要列表
        """
        result = await self.session.execute(
            select(MeetingMinutes)
            .where(
                and_(
                    MeetingMinutes.project_id == project_id,
                    MeetingMinutes.meeting_title.ilike(f"%{keyword}%"),
                    MeetingMinutes.is_current == True,
                )
            )
            .order_by(desc(MeetingMinutes.meeting_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())