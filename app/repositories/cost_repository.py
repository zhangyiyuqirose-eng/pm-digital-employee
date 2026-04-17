"""
PM Digital Employee - Cost Repository
项目经理数字员工系统 - 成本数据访问层
"""

import uuid
from typing import Any, Dict, List, Optional
from decimal import Decimal
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import ProjectScopedRepository
from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
from app.domain.enums import CostCategory
from app.core.logging import get_logger

logger = get_logger(__name__)


class CostBudgetRepository(ProjectScopedRepository[ProjectCostBudget]):
    """
    成本预算Repository.

    提成本预算数据的CRUD操作，强制project_id过滤。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化成本预算Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(ProjectCostBudget, session)

    async def list_by_category(
        self,
        project_id: uuid.UUID,
        category: CostCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectCostBudget]:
        """
        查询指定类别的预算列表.

        Args:
            project_id: 项目ID（必填）
            category: 成本类别
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectCostBudget]: 预算列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"category": category},
            skip=skip,
            limit=limit,
        )

    async def get_total_budget(
        self,
        project_id: uuid.UUID,
    ) -> Decimal:
        """
        获取项目总预算.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Decimal: 总预算金额
        """
        try:
            result = await self.session.execute(
                select(func.coalesce(func.sum(ProjectCostBudget.amount), 0)).where(
                    ProjectCostBudget.project_id == project_id
                )
            )
            return Decimal(str(result.scalar() or 0))
        except Exception as exc:
            logger.error("Failed to get total budget", project_id=str(project_id), error=str(exc))
            raise

    async def get_budget_by_category(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Decimal]:
        """
        按类别获取预算汇总.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 各类别的预算金额
        """
        try:
            result = await self.session.execute(
                select(
                    ProjectCostBudget.category,
                    func.sum(ProjectCostBudget.amount).label('total')
                ).where(ProjectCostBudget.project_id == project_id)
                .group_by(ProjectCostBudget.category)
            )

            rows = result.all()
            return {row.category: Decimal(str(row.total or 0)) for row in rows}
        except Exception as exc:
            logger.error("Failed to get budget by category", project_id=str(project_id), error=str(exc))
            raise


class CostActualRepository(ProjectScopedRepository[ProjectCostActual]):
    """
    成本实际支出Repository.

    提供成本实际数据的CRUD操作，强制project_id过滤。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化成本实际Repository.

        Args:
            session: 数据库会话
        """
        super().__init__(ProjectCostActual, session)

    async def list_by_category(
        self,
        project_id: uuid.UUID,
        category: CostCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectCostActual]:
        """
        查询指定类别的实际支出列表.

        Args:
            project_id: 项目ID（必填）
            category: 成本类别
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectCostActual]: 实际支出列表
        """
        return await self.list_by_project(
            project_id=project_id,
            filters={"category": category},
            skip=skip,
            limit=limit,
        )

    async def get_total_actual(
        self,
        project_id: uuid.UUID,
    ) -> Decimal:
        """
        获取项目总实际支出.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Decimal: 总实际支出金额
        """
        try:
            result = await self.session.execute(
                select(func.coalesce(func.sum(ProjectCostActual.amount), 0)).where(
                    ProjectCostActual.project_id == project_id
                )
            )
            return Decimal(str(result.scalar() or 0))
        except Exception as exc:
            logger.error("Failed to get total actual", project_id=str(project_id), error=str(exc))
            raise

    async def get_actual_by_category(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Decimal]:
        """
        按类别获取实际支出汇总.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 各类别的实际支出金额
        """
        try:
            result = await self.session.execute(
                select(
                    ProjectCostActual.category,
                    func.sum(ProjectCostActual.amount).label('total')
                ).where(ProjectCostActual.project_id == project_id)
                .group_by(ProjectCostActual.category)
            )

            rows = result.all()
            return {row.category: Decimal(str(row.total or 0)) for row in rows}
        except Exception as exc:
            logger.error("Failed to get actual by category", project_id=str(project_id), error=str(exc))
            raise

    async def get_cost_variance(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取成本偏差信息.

        Args:
            project_id: 项目ID（必填）

        Returns:
            Dict: 成本偏差信息
        """
        try:
            # 获取总预算
            budget_result = await self.session.execute(
                select(func.coalesce(func.sum(ProjectCostBudget.amount), 0)).where(
                    ProjectCostBudget.project_id == project_id
                )
            )
            budget = Decimal(str(budget_result.scalar() or 0))

            # 获取总实际
            actual_result = await self.session.execute(
                select(func.coalesce(func.sum(ProjectCostActual.amount), 0)).where(
                    ProjectCostActual.project_id == project_id
                )
            )
            actual = Decimal(str(actual_result.scalar() or 0))

            variance = budget - actual
            variance_percent = (variance / budget * 100) if budget > 0 else Decimal('0')

            return {
                "budget": budget,
                "actual": actual,
                "variance": variance,
                "variance_percent": float(variance_percent),
                "is_over_budget": actual > budget,
            }
        except Exception as exc:
            logger.error("Failed to get cost variance", project_id=str(project_id), error=str(exc))
            raise