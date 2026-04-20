"""
PM Digital Employee - Weekly Report Repository
项目经理数字员工系统 - 周报数据仓库

提供周报数据的CRUD操作，遵循项目级数据隔离原则。
"""

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DataNotFoundError
from app.core.logging import get_logger
from app.domain.enums import DataSource, WeeklyReportStatus
from app.domain.models.weekly_report import WeeklyReport
from app.repositories.base import ProjectScopedRepository

logger = get_logger(__name__)


class WeeklyReportRepository(ProjectScopedRepository[WeeklyReport]):
    """
    周报数据仓库.

    继承ProjectScopedRepository，强制project_id过滤。
    提供周报的CRUD操作和查询功能。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化周报数据仓库.

        Args:
            session: 数据库会话
        """
        super().__init__(WeeklyReport, session)

    async def generate_report_code(self, project_id: uuid.UUID) -> str:
        """
        生成周报编码.

        格式：WR-YYYYMMDD-NNN（WR为周报缩写，YYYYMMDD为日期，NNN为序号）

        Args:
            project_id: 项目ID

        Returns:
            str: 周报编码
        """
        today = date.today()
        date_str = today.strftime("%Y%m%d")

        # 查询当天已有周报数量
        result = await self.session.execute(
            select(func.count(WeeklyReport.id))
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.report_code.like(f"WR-{date_str}%")
                )
            )
        )
        count = result.scalar() or 0

        # 生成编码
        code = f"WR-{date_str}-{count + 1:03d}"
        return code

    async def get_current_reports(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WeeklyReport]:
        """
        获取项目当前版本周报列表.

        Args:
            project_id: 项目ID
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            List[WeeklyReport]: 周报列表
        """
        result = await self.session.execute(
            select(WeeklyReport)
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.is_current == True,
                )
            )
            .order_by(desc(WeeklyReport.report_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        project_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> List[WeeklyReport]:
        """
        获取指定日期范围内的周报.

        Args:
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[WeeklyReport]: 周报列表
        """
        result = await self.session.execute(
            select(WeeklyReport)
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.week_start >= start_date,
                    WeeklyReport.week_end <= end_date,
                    WeeklyReport.is_current == True,
                )
            )
            .order_by(desc(WeeklyReport.week_start))
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        project_id: uuid.UUID,
        status: WeeklyReportStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WeeklyReport]:
        """
        获取指定状态的周报列表.

        Args:
            project_id: 项目ID
            status: 周报状态
            skip: 跳过数量
            limit: 返回数量限制

        Returns:
            List[WeeklyReport]: 周报列表
        """
        result = await self.session.execute(
            select(WeeklyReport)
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.status == status,
                    WeeklyReport.is_current == True,
                )
            )
            .order_by(desc(WeeklyReport.report_date))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_external_id(
        self,
        external_id: str,
    ) -> Optional[WeeklyReport]:
        """
        根据外部系统ID查询周报.

        Args:
            external_id: 外部系统ID（飞书表格行ID等）

        Returns:
            Optional[WeeklyReport]: 周报对象或None
        """
        result = await self.session.execute(
            select(WeeklyReport)
            .where(WeeklyReport.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def update_sync_info(
        self,
        report_id: uuid.UUID,
        sync_version: int,
        external_id: Optional[str] = None,
    ) -> WeeklyReport:
        """
        更新同步信息.

        Args:
            report_id: 周报ID
            sync_version: 同步版本号
            external_id: 外部系统ID

        Returns:
            WeeklyReport: 更新后的周报

        Raises:
            DataNotFoundError: 周报不存在
        """
        report = await self.get_by_id(report_id)
        if report is None:
            raise DataNotFoundError(f"周报不存在: {report_id}")

        report.sync_version = sync_version
        report.last_sync_at = datetime.now(timezone.utc)
        if external_id:
            report.external_id = external_id

        await self.session.flush()
        return report

    async def mark_as_history(
        self,
        report_id: uuid.UUID,
    ) -> None:
        """
        将周报标记为历史版本.

        Args:
            report_id: 周报ID
        """
        result = await self.session.execute(
            select(WeeklyReport).where(WeeklyReport.id == report_id)
        )
        report = result.scalar_one_or_none()

        if report:
            report.is_current = False
            await self.session.flush()

    async def count_by_project(
        self,
        project_id: uuid.UUID,
    ) -> int:
        """
        统计项目周报数量.

        Args:
            project_id: 项目ID

        Returns:
            int: 周报数量
        """
        result = await self.session.execute(
            select(func.count(WeeklyReport.id))
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.is_current == True,
                )
            )
        )
        return result.scalar() or 0

    async def get_latest_report(
        self,
        project_id: uuid.UUID,
    ) -> Optional[WeeklyReport]:
        """
        获取项目最新周报.

        Args:
            project_id: 项目ID

        Returns:
            Optional[WeeklyReport]: 最新周报或None
        """
        result = await self.session.execute(
            select(WeeklyReport)
            .where(
                and_(
                    WeeklyReport.project_id == project_id,
                    WeeklyReport.is_current == True,
                )
            )
            .order_by(desc(WeeklyReport.report_date))
            .limit(1)
        )
        return result.scalar_one_or_none()