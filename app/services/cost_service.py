"""
PM Digital Employee - Cost Service
项目经理数字员工系统 - 成本业务服务
"""

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, CostNotFoundError, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import CostCategory
from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
from app.repositories.cost_repository import CostBudgetRepository, CostActualRepository
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)


class CostService:
    """
    成本业务服务.

    封装成本相关的业务逻辑，包括预算和实际支出。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化成本服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._budget_repository = CostBudgetRepository(session)
        self._actual_repository = CostActualRepository(session)
        self._project_repository = ProjectRepository(session)

    # ==================== 预算操作 ====================

    async def create_budget(
        self,
        project_id: uuid.UUID,
        category: CostCategory,
        amount: Decimal,
        description: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> ProjectCostBudget:
        """
        创建预算记录.

        Args:
            project_id: 项目ID（必填）
            category: 成本类别（必填）
            amount: 预算金额（必填）
            description: 描述
            fiscal_year: 财年
            user_id: 创建用户ID

        Returns:
            ProjectCostBudget: 创建的预算

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 创建预算数据（移除created_at/updated_at，ProjectCostBudget模型中无这些字段）
        budget_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "category": category,
            "amount": amount,
            "description": description,
            "fiscal_year": fiscal_year,
        }

        budget = await self._budget_repository.create_in_project(project_id, budget_data)

        logger.info(
            "Budget created",
            extra={
                "budget_id": str(budget.id),
                "project_id": str(project_id),
                "category": category,
                "amount": float(amount),
            }
        )

        return budget

    async def get_budget(
        self,
        budget_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectCostBudget:
        """
        获取预算记录.

        Args:
            budget_id: 预算ID
            project_id: 项目ID

        Returns:
            ProjectCostBudget: 预算对象

        Raises:
            CostNotFoundError: 预算不存在
        """
        budget = await self._budget_repository.get_by_id_or_error(budget_id, project_id)
        return budget

    async def update_budget(
        self,
        budget_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> ProjectCostBudget:
        """
        更新预算记录.

        Args:
            budget_id: 预算ID
            project_id: 项目ID
            **kwargs: 更新字段

        Returns:
            ProjectCostBudget: 更新后的预算
        """
        budget = await self._budget_repository.update_in_project(budget_id, project_id, kwargs)

        logger.info(
            "Budget updated",
            extra={
                "budget_id": str(budget_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return budget

    async def list_budgets(
        self,
        project_id: uuid.UUID,
        category: Optional[CostCategory] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectCostBudget]:
        """
        列出预算记录.

        Args:
            project_id: 项目ID
            category: 成本类别过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectCostBudget]: 预算列表
        """
        filters = {}
        if category:
            filters["category"] = category

        return await self._budget_repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
        )

    async def delete_budget(
        self,
        budget_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除预算记录.

        Args:
            budget_id: 预算ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        return await self._budget_repository.delete_in_project(budget_id, project_id)

    # ==================== 实际支出操作 ====================

    async def create_actual(
        self,
        project_id: uuid.UUID,
        category: CostCategory,
        amount: Decimal,
        expense_date: date,
        description: Optional[str] = None,
        invoice_number: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ProjectCostActual:
        """
        创建实际支出记录.

        Args:
            project_id: 项目ID（必填）
            category: 成本类别（必填）
            amount: 实际金额（必填）
            expense_date: 支出日期（必填）
            description: 描述
            invoice_number: 发票号
            user_id: 创建用户ID

        Returns:
            ProjectCostActual: 创建的实际支出

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 创建实际支出数据（移除created_at/updated_at，ProjectCostActual模型中无这些字段）
        actual_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "category": category,
            "amount": amount,
            "expense_date": expense_date,
            "description": description,
            "invoice_number": invoice_number,
            "approval_status": "pending",
        }

        actual = await self._actual_repository.create_in_project(project_id, actual_data)

        logger.info(
            "Actual cost created",
            extra={
                "actual_id": str(actual.id),
                "project_id": str(project_id),
                "category": category,
                "amount": float(amount),
                "expense_date": str(expense_date),
            }
        )

        return actual

    async def get_actual(
        self,
        actual_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectCostActual:
        """
        获取实际支出记录.

        Args:
            actual_id: 实际支出ID
            project_id: 项目ID

        Returns:
            ProjectCostActual: 实际支出对象

        Raises:
            CostNotFoundError: 实际支出不存在
        """
        actual = await self._actual_repository.get_by_id_or_error(actual_id, project_id)
        return actual

    async def update_actual(
        self,
        actual_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> ProjectCostActual:
        """
        更新实际支出记录.

        Args:
            actual_id: 实际支出ID
            project_id: 项目ID
            **kwargs: 更新字段

        Returns:
            ProjectCostActual: 更新后的实际支出
        """
        actual = await self._actual_repository.update_in_project(actual_id, project_id, kwargs)

        logger.info(
            "Actual cost updated",
            extra={
                "actual_id": str(actual_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return actual

    async def list_actuals(
        self,
        project_id: uuid.UUID,
        category: Optional[CostCategory] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectCostActual]:
        """
        列出实际支出记录.

        Args:
            project_id: 项目ID
            category: 成本类别过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectCostActual]: 实际支出列表
        """
        filters = {}
        if category:
            filters["category"] = category

        return await self._actual_repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
        )

    async def delete_actual(
        self,
        actual_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除实际支出记录.

        Args:
            actual_id: 实际支出ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        return await self._actual_repository.delete_in_project(actual_id, project_id)

    # ==================== 成本汇总 ====================

    async def get_cost_summary(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取成本汇总.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 成本汇总信息
        """
        return await self._actual_repository.get_cost_variance(project_id)

    async def get_budget_by_category(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Decimal]:
        """
        按类别获取预算汇总.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 各类别的预算金额
        """
        return await self._budget_repository.get_budget_by_category(project_id)

    async def get_actual_by_category(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Decimal]:
        """
        按类别获取实际支出汇总.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 各类别的实际支出金额
        """
        return await self._actual_repository.get_actual_by_category(project_id)