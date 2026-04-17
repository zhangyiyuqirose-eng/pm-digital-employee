"""
PM Digital Employee - Unit of Work Pattern
项目经理数字员工系统 - 工作单元模式

实现事务边界管理，确保多表操作的原子性。
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class UnitOfWork:
    """
    工作单元模式.

    提供事务边界管理，确保多表操作的原子性。
    使用方式：
    
    ```python
    async with unit_of_work.begin():
        project = await project_repo.create(data)
        role = await role_repo.create_role(user_id, project_id)
        # 全部成功或全部回滚
    ```
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化工作单元.

        Args:
            session: 数据库会话
        """
        self._session = session
        self._committed = False
        self._rolled_back = False

    @property
    def session(self) -> AsyncSession:
        """获取数据库会话."""
        return self._session

    @property
    def is_active(self) -> bool:
        """检查工作单元是否活跃."""
        return not self._committed and not self._rolled_back

    async def begin(self) -> None:
        """
        开始事务.

        对于AsyncSession，事务在首次操作时自动开始。
        此方法主要用于标记事务边界。
        """
        logger.debug("UnitOfWork transaction boundary started")
        self._committed = False
        self._rolled_back = False

    async def commit(self) -> None:
        """
        提交事务.

        将所有更改持久化到数据库。

        Raises:
            DatabaseError: 提交失败
        """
        if self._committed:
            logger.warning("UnitOfWork already committed")
            return

        if self._rolled_back:
            raise DatabaseError(message="Cannot commit after rollback")

        try:
            await self._session.commit()
            self._committed = True
            logger.debug("UnitOfWork committed successfully")
        except Exception as exc:
            logger.error("UnitOfWork commit failed", error=str(exc))
            raise DatabaseError(message="事务提交失败", code=None) from exc

    async def rollback(self) -> None:
        """
        回滚事务.

        撤销所有未提交的更改。

        Raises:
            DatabaseError: 回滚失败
        """
        if self._rolled_back:
            logger.warning("UnitOfWork already rolled back")
            return

        if self._committed:
            raise DatabaseError(message="Cannot rollback after commit")

        try:
            await self._session.rollback()
            self._rolled_back = True
            logger.debug("UnitOfWork rolled back successfully")
        except Exception as exc:
            logger.error("UnitOfWork rollback failed", error=str(exc))
            raise DatabaseError(message="事务回滚失败", code=None) from exc

    async def flush(self) -> None:
        """
        刷新到数据库但不提交.

        用于获取自动生成的ID等。

        Raises:
            DatabaseError: 刷新失败
        """
        try:
            await self._session.flush()
            logger.debug("UnitOfWork flushed")
        except Exception as exc:
            logger.error("UnitOfWork flush failed", error=str(exc))
            raise DatabaseError(message="事务刷新失败", code=None) from exc

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator["UnitOfWork", None]:
        """
        事务上下文管理器.

        自动管理事务边界：
        - 正常退出时提交
        - 异常时回滚

        Yields:
            UnitOfWork: 工作单元实例

        Example:
            ```python
            async with uow.transaction():
                await repo1.create(data1)
                await repo2.create(data2)
            # 自动提交或回滚
            ```
        """
        await self.begin()
        try:
            yield self
            await self.commit()
        except Exception:
            await self.rollback()
            raise


class UnitOfWorkManager:
    """
    工作单元管理器.

    提供工作单元的创建和管理。
    """

    def __init__(self, session_factory: callable) -> None:
        """
        初始化管理器.

        Args:
            session_factory: 数据库会话工厂函数
        """
        self._session_factory = session_factory

    @asynccontextmanager
    async def create(self) -> AsyncGenerator[UnitOfWork, None]:
        """
        创建新的工作单元.

        Yields:
            UnitOfWork: 新的工作单元实例
        """
        session = self._session_factory()
        uow = UnitOfWork(session)
        
        try:
            yield uow
            if uow.is_active:
                await uow.commit()
        except Exception:
            if uow.is_active:
                await uow.rollback()
            raise
        finally:
            await session.close()


# 便捷函数
def create_unit_of_work(session: AsyncSession) -> UnitOfWork:
    """
    创建工作单元.

    Args:
        session: 数据库会话

    Returns:
        UnitOfWork: 工作单元实例
    """
    return UnitOfWork(session)