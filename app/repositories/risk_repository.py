"""
PM Digital Employee - Risk Repository
项目经理数字员工系统 - 风险数据访问层
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import ProjectScopedRepository
from app.domain.models.risk import ProjectRisk
from app.domain.enums import RiskLevel, RiskStatus, RiskCategory
from app.core.logging import get_logger

logger = get_logger(__name__)


class RiskRepository(ProjectScopedRepository[ProjectRisk]):
    """
    风险Repository.

    提供风险数据的CRUD操作，强制project_id过滤。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化风险Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(ProjectRisk, session)

    async def list_by_level(
        self,
        project_id: uuid.UUID,
        level: RiskLevel,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectRisk]:
        """
        查询指定等级的风险列表.

        Args:
            project_id: 项目ID（必填）
            level: 风险等级
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectRisk]: 风险列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"level": level},
            skip=skip,
            limit=limit,
        )

    async def list_by_status(
        self,
        project_id: uuid.UUID,
        status: RiskStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectRisk]:
        """
        查询指定状态的风险列表.

        Args:
            project_id: 项目ID（必填）
            status: 风险状态
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectRisk]: 风险列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"status": status},
            skip=skip,
            limit=limit,
        )

    async def list_high_risks(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectRisk]:
        """
        查询高风险列表.

        Args:
            project_id: 项目ID（必填）
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectRisk]: 高风险列表
        """
        try:
            query = select(ProjectRisk).where(
                and_(
                    ProjectRisk.project_id == project_id,
                    ProjectRisk.level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
                )
            ).offset(skip).limit(limit).order_by(ProjectRisk.probability.desc())

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to list high risks", project_id=str(project_id), error=str(exc))
            raise

    async def list_by_owner(
        self,
        project_id: uuid.UUID,
        owner_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectRisk]:
        """
        查询指定负责人的风险列表.

        Args:
            project_id: 项目ID（必填）
            owner_id: 负责人飞书用户ID
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectRisk]: 风险列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"owner_id": owner_id},
            skip=skip,
            limit=limit,
        )

    async def count_by_level(
        self,
        project_id: uuid.UUID,
        level: Optional[RiskLevel] = None,
    ) -> int:
        """
        统计风险数量.

        Args:
            project_id: 项目ID（必填）
            level: 风险等级过滤

        Returns:
            int: 风险数量
        """
        filters = {}
        if level:
            filters["level"] = level

        return await self.count_by_project(project_id=project_id, filters=filters)

    async def get_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取风险统计信息.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 统计信息
        """
        from sqlalchemy import case

        try:
            result = await self.session.execute(
                select(
                    func.count(ProjectRisk.id).label('total'),
                    func.sum(case((ProjectRisk.level == RiskLevel.HIGH, 1), else_=0)).label('high'),
                    func.sum(case((ProjectRisk.level == RiskLevel.MEDIUM, 1), else_=0)).label('medium'),
                    func.sum(case((ProjectRisk.level == RiskLevel.LOW, 1), else_=0)).label('low'),
                    func.sum(case((ProjectRisk.status == RiskStatus.IDENTIFIED, 1), else_=0)).label('identified'),
                    func.sum(case((ProjectRisk.status == RiskStatus.MITIGATING, 1), else_=0)).label('mitigating'),
                    func.sum(case((ProjectRisk.status == RiskStatus.RESOLVED, 1), else_=0)).label('resolved'),
                ).where(ProjectRisk.project_id == project_id)
            )

            row = result.first()
            if row:
                return {
                    "total": row.total or 0,
                    "high": row.high or 0,
                    "medium": row.medium or 0,
                    "low": row.low or 0,
                    "identified": row.identified or 0,
                    "mitigating": row.mitigating or 0,
                    "resolved": row.resolved or 0,
                }
            return {"total": 0, "high": 0, "medium": 0, "low": 0, "identified": 0, "mitigating": 0, "resolved": 0}
        except Exception as exc:
            logger.error("Failed to get risk statistics", project_id=str(project_id), error=str(exc))
            raise

    async def generate_risk_code(
        self,
        project_id: uuid.UUID,
    ) -> str:
        """
        生成风险编码.

        格式: RSK-NNN（项目内递增）

        Args:
            project_id: 项目ID

        Returns:
            str: 风险编码
        """
        try:
            result = await self.session.execute(
                select(func.count(ProjectRisk.id)).where(ProjectRisk.project_id == project_id)
            )
            count = result.scalar() or 0
            seq_num = count + 1
            return f"RSK-{seq_num:03d}"
        except Exception:
            return f"RSK-{uuid.uuid4().hex[:6]}"