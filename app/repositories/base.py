"""
PM Digital Employee - Base Repository Module
项目经理数字员工系统 - Repository基类模块

实现强制project_id过滤的Repository基类，
确保所有数据查询都遵循项目级隔离原则。
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.exceptions import DataNotFoundError, DatabaseError, ProjectAccessDeniedError
from app.core.logging import get_logger
from app.domain.base import Base

logger = get_logger(__name__)

# 泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType], ABC):
    """
    Repository基类.

    提供通用的CRUD操作，所有Repository必须继承此类。
    不涉及project_id过滤的通用操作。

    Attributes:
        model: ORM模型类
        session: 数据库会话
    """

    def __init__(self, model: Type[ModelType], session: Union[AsyncSession, Session]) -> None:
        """
        初始化Repository.

        Args:
            model: ORM模型类
            session: 数据库会话
        """
        self.model = model
        self.session = session

    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        创建记录.

        Args:
            data: 创建数据字典

        Returns:
            ModelType: 创建的记录

        Raises:
            DatabaseError: 数据库操作错误
        """
        try:
            instance = self.model(**data)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except Exception as exc:
            logger.error("Failed to create record", model=self.model.__name__, error=str(exc))
            raise DatabaseError(message=f"创建{self.model.__name__}失败", cause=exc)

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        """
        根据ID查询记录.

        Args:
            id: 记录ID

        Returns:
            Optional[ModelType]: 查询结果或None
        """
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Failed to get by id", model=self.model.__name__, id=str(id), error=str(exc))
            raise DatabaseError(message=f"查询{self.model.__name__}失败", cause=exc)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> List[ModelType]:
        """
        查询所有记录（分页）.

        Args:
            skip: 跳过数量
            limit: 返回数量
            order_by: 排序字段

        Returns:
            List[ModelType]: 记录列表
        """
        try:
            query = select(self.model).offset(skip).limit(limit)
            if order_by is not None:
                query = query.order_by(order_by)
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Failed to get all", model=self.model.__name__, error=str(exc))
            raise DatabaseError(message=f"查询{self.model.__name__}列表失败", cause=exc)

    async def update(self, id: uuid.UUID, data: Dict[str, Any]) -> ModelType:
        """
        更新记录.

        Args:
            id: 记录ID
            data: 更新数据字典

        Returns:
            ModelType: 更新后的记录

        Raises:
            DataNotFoundError: 记录不存在
        """
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                raise DataNotFoundError(resource_type=self.model.__name__, resource_id=str(id))

            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            instance.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except DataNotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to update", model=self.model.__name__, id=str(id), error=str(exc))
            raise DatabaseError(message=f"更新{self.model.__name__}失败", cause=exc)

    async def delete(self, id: uuid.UUID) -> bool:
        """
        删除记录.

        Args:
            id: 记录ID

        Returns:
            bool: 是否删除成功

        Raises:
            DataNotFoundError: 记录不存在
        """
        try:
            instance = await self.get_by_id(id)
            if instance is None:
                raise DataNotFoundError(resource_type=self.model.__name__, resource_id=str(id))

            await self.session.delete(instance)
            await self.session.flush()
            return True
        except DataNotFoundError:
            raise
        except Exception as exc:
            logger.error("Failed to delete", model=self.model.__name__, id=str(id), error=str(exc))
            raise DatabaseError(message=f"删除{self.model.__name__}失败", cause=exc)

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数量.

        Args:
            filters: 过滤条件

        Returns:
            int: 记录数量
        """
        try:
            query = select(func.count()).select_from(self.model)
            if filters:
                conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
                if conditions:
                    query = query.where(and_(*conditions))
            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as exc:
            logger.error("Failed to count", model=self.model.__name__, error=str(exc))
            raise DatabaseError(message=f"统计{self.model.__name__}失败", cause=exc)


class ProjectScopedRepository(BaseRepository[ModelType]):
    """
    项目隔离Repository基类.

    强制所有查询操作携带project_id参数，
    确保项目级数据隔离，防止跨项目数据访问。

    所有涉及项目数据的Repository必须继承此类。

    使用方式:
        class TaskRepository(ProjectScopedRepository[Task]):
            async def get_by_status(self, project_id: uuid.UUID, status: str) -> List[Task]:
                return await self.list_by_project(project_id, filters={"status": status})
    """

    def __init__(self, model: Type[ModelType], session: Union[AsyncSession, Session]) -> None:
        """
        初始化Repository.

        Args:
            model: ORM模型类（必须有project_id字段）
            session: 数据库会话

        Raises:
            ValueError: 模型没有project_id字段
        """
        super().__init__(model, session)

        # 验证模型是否有project_id字段
        if not hasattr(model, "project_id"):
            raise ValueError(f"Model {model.__name__} must have project_id field for ProjectScopedRepository")

    async def get_by_id_with_project(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Optional[ModelType]:
        """
        根据ID和project_id查询记录.

        强制检查project_id，确保只能查询当前项目的数据。

        Args:
            id: 记录ID
            project_id: 项目ID

        Returns:
            Optional[ModelType]: 查询结果或None
        """
        try:
            result = await self.session.execute(
                select(self.model).where(
                    and_(
                        self.model.id == id,
                        self.model.project_id == project_id,
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(
                "Failed to get by id with project",
                model=self.model.__name__,
                id=str(id),
                project_id=str(project_id),
                error=str(exc),
            )
            raise DatabaseError(message=f"查询{self.model.__name__}失败", cause=exc)

    async def get_by_id_or_error(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ModelType:
        """
        根据ID和project_id查询记录，不存在则抛出异常.

        Args:
            id: 记录ID
            project_id: 项目ID

        Returns:
            ModelType: 查询结果

        Raises:
            DataNotFoundError: 记录不存在
            ProjectAccessDeniedError: 项目ID不匹配
        """
        instance = await self.get_by_id_with_project(id, project_id)
        if instance is None:
            # 先检查记录是否存在
            instance_without_project = await super().get_by_id(id)
            if instance_without_project is not None:
                # 记录存在但项目ID不匹配
                raise ProjectAccessDeniedError(
                    project_id=str(project_id),
                    trace_id=None,
                )
            raise DataNotFoundError(resource_type=self.model.__name__, resource_id=str(id))
        return instance

    async def list_by_project(
        self,
        project_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> List[ModelType]:
        """
        查询指定项目的记录列表.

        Args:
            project_id: 项目ID（必填）
            filters: 额外过滤条件
            skip: 跳过数量
            limit: 返回数量
            order_by: 排序字段

        Returns:
            List[ModelType]: 记录列表
        """
        if project_id is None:
            raise ValueError("project_id is required for ProjectScopedRepository.list_by_project")

        try:
            query = select(self.model).where(self.model.project_id == project_id)

            # 添加额外过滤条件
            if filters:
                conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
                if conditions:
                    query = query.where(and_(*conditions))

            # 排序
            if order_by is not None:
                query = query.order_by(order_by)
            else:
                # 默认按创建时间倒序
                if hasattr(self.model, "created_at"):
                    query = query.order_by(self.model.created_at.desc())

            # 分页
            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "Failed to list by project",
                model=self.model.__name__,
                project_id=str(project_id),
                error=str(exc),
            )
            raise DatabaseError(message=f"查询{self.model.__name__}列表失败", cause=exc)

    async def count_by_project(
        self,
        project_id: uuid.UUID,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        统计指定项目的记录数量.

        Args:
            project_id: 项目ID（必填）
            filters: 额外过滤条件

        Returns:
            int: 记录数量
        """
        if project_id is None:
            raise ValueError("project_id is required for ProjectScopedRepository.count_by_project")

        try:
            query = select(func.count()).select_from(self.model).where(self.model.project_id == project_id)

            if filters:
                conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
                if conditions:
                    query = query.where(and_(*conditions))

            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as exc:
            logger.error(
                "Failed to count by project",
                model=self.model.__name__,
                project_id=str(project_id),
                error=str(exc),
            )
            raise DatabaseError(message=f"统计{self.model.__name__}失败", cause=exc)

    async def create_in_project(
        self,
        project_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> ModelType:
        """
        在指定项目中创建记录.

        自动注入project_id，确保记录属于正确的项目。

        Args:
            project_id: 项目ID（必填）
            data: 创建数据字典

        Returns:
            ModelType: 创建的记录
        """
        if project_id is None:
            raise ValueError("project_id is required for ProjectScopedRepository.create_in_project")

        # 自动注入project_id
        data["project_id"] = project_id
        return await self.create(data)

    async def update_in_project(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
        data: Dict[str, Any],
    ) -> ModelType:
        """
        更新指定项目中的记录.

        强制检查project_id，防止跨项目修改。

        Args:
            id: 记录ID
            project_id: 项目ID（必填）
            data: 更新数据字典

        Returns:
            ModelType: 更新后的记录

        Raises:
            DataNotFoundError: 记录不存在
            ProjectAccessDeniedError: 项目ID不匹配
        """
        if project_id is None:
            raise ValueError("project_id is required for ProjectScopedRepository.update_in_project")

        # 先获取并验证项目归属
        instance = await self.get_by_id_or_error(id, project_id)

        # 更新数据
        for key, value in data.items():
            if key != "project_id" and hasattr(instance, key):  # 禁止修改project_id
                setattr(instance, key, value)

        instance.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete_in_project(
        self,
        id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除指定项目中的记录.

        强制检查project_id，防止跨项目删除。

        Args:
            id: 记录ID
            project_id: 项目ID（必填）

        Returns:
            bool: 是否删除成功

        Raises:
            DataNotFoundError: 记录不存在
            ProjectAccessDeniedError: 项目ID不匹配
        """
        if project_id is None:
            raise ValueError("project_id is required for ProjectScopedRepository.delete_in_project")

        # 先获取并验证项目归属
        instance = await self.get_by_id_or_error(id, project_id)

        await self.session.delete(instance)
        await self.session.flush()
        return True