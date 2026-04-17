"""
PM Digital Employee - Risk Service
项目经理数字员工系统 - 风险业务服务
"""

import uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, RiskNotFoundError, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import RiskLevel, RiskStatus, RiskCategory
from app.domain.models.risk import ProjectRisk
from app.repositories.risk_repository import RiskRepository
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)


class RiskService:
    """
    风险业务服务.

    封装风险相关的业务逻辑。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化风险服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = RiskRepository(session)
        self._project_repository = ProjectRepository(session)

    async def create_risk(
        self,
        project_id: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        level: RiskLevel = RiskLevel.MEDIUM,
        category: RiskCategory = RiskCategory.SCHEDULE,
        probability: int = 3,
        impact: int = 3,
        mitigation_plan: Optional[str] = None,
        owner_id: Optional[str] = None,
        owner_name: Optional[str] = None,
        due_date: Optional[date] = None,
        user_id: Optional[str] = None,
    ) -> ProjectRisk:
        """
        创建风险.

        Args:
            project_id: 项目ID（必填）
            title: 风险标题（必填）
            description: 风险描述
            level: 风险等级
            category: 风险类别
            probability: 发生概率（1-5）
            impact: 影响程度（1-5）
            mitigation_plan: 应对措施
            owner_id: 负责人飞书用户ID
            owner_name: 负责人姓名
            due_date: 预计解决日期
            user_id: 创建用户ID

        Returns:
            ProjectRisk: 创建的风险

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 生成风险编码
        code = await self._repository.generate_risk_code(project_id)

        # 创建风险数据（移除created_at/updated_at，ProjectRisk模型中无这些字段）
        risk_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "code": code,
            "title": title,
            "description": description,
            "level": level,
            "category": category,
            "probability": probability,
            "impact": impact,
            "status": RiskStatus.IDENTIFIED,
            "identified_date": date.today(),
            "mitigation_plan": mitigation_plan,
            "owner_id": owner_id,
            "owner_name": owner_name,
            "due_date": due_date,
        }

        risk = await self._repository.create_in_project(project_id, risk_data)

        logger.info(
            "Risk created",
            extra={
                "risk_id": str(risk.id),
                "project_id": str(project_id),
                "title": title,
                "level": level,
            }
        )

        return risk

    async def get_risk(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectRisk:
        """
        获取风险信息.

        Args:
            risk_id: 风险ID
            project_id: 项目ID（用于权限检查）

        Returns:
            ProjectRisk: 风险对象

        Raises:
            RiskNotFoundError: 风险不存在
        """
        risk = await self._repository.get_by_id_or_error(risk_id, project_id)
        return risk

    async def update_risk(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> ProjectRisk:
        """
        更新风险.

        Args:
            risk_id: 风险ID
            project_id: 项目ID（用于权限检查）
            **kwargs: 更新字段

        Returns:
            ProjectRisk: 更新后的风险

        Raises:
            RiskNotFoundError: 风险不存在
        """
        risk = await self._repository.update_in_project(risk_id, project_id, kwargs)

        logger.info(
            "Risk updated",
            extra={
                "risk_id": str(risk_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return risk

    async def resolve_risk(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
        resolution_note: Optional[str] = None,
    ) -> ProjectRisk:
        """
        解决风险.

        Args:
            risk_id: 风险ID
            project_id: 项目ID
            resolution_note: 解决说明

        Returns:
            ProjectRisk: 更新后的风险
        """
        update_data = {
            "status": RiskStatus.RESOLVED,
            "resolved_date": date.today(),
        }

        if resolution_note:
            update_data["root_cause"] = resolution_note

        return await self.update_risk(risk_id, project_id, **update_data)

    async def acknowledge_risk(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectRisk:
        """
        确认风险.

        Args:
            risk_id: 风险ID
            project_id: 项目ID

        Returns:
            ProjectRisk: 更新后的风险
        """
        return await self.update_risk(
            risk_id,
            project_id,
            status=RiskStatus.ANALYZING,
        )

    async def start_mitigation(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ProjectRisk:
        """
        开始处理风险.

        Args:
            risk_id: 风险ID
            project_id: 项目ID

        Returns:
            ProjectRisk: 更新后的风险
        """
        return await self.update_risk(
            risk_id,
            project_id,
            status=RiskStatus.MITIGATING,
        )

    async def list_risks(
        self,
        project_id: uuid.UUID,
        level: Optional[RiskLevel] = None,
        status: Optional[RiskStatus] = None,
        owner_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ProjectRisk]:
        """
        列出风险.

        Args:
            project_id: 项目ID
            level: 风险等级过滤
            status: 风险状态过滤
            owner_id: 负责人过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[ProjectRisk]: 风险列表
        """
        filters = {}
        if level:
            filters["level"] = level
        if status:
            filters["status"] = status
        if owner_id:
            filters["owner_id"] = owner_id

        return await self._repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
        )

    async def get_risk_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取风险统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        return await self._repository.get_statistics(project_id)

    async def delete_risk(
        self,
        risk_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除风险.

        Args:
            risk_id: 风险ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        return await self._repository.delete_in_project(risk_id, project_id)