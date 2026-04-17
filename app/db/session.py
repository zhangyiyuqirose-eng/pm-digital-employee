"""
PM Digital Employee - Database Session Module
Database connection pool and session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
import asyncio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 数据库连接池配置
DB_POOL_CONFIG = {
    "pool_size": settings.database.pool_size,  # 连接池大小
    "max_overflow": settings.database.max_overflow,  # 最大溢出连接数
    "pool_pre_ping": True,  # 连接预检测
    "pool_recycle": settings.database.pool_recycle,  # 连接回收时间（秒）
    "pool_timeout": settings.database.pool_timeout,
    "echo": settings.is_development,  # 生产环境应关闭SQL日志
    "poolclass": AsyncAdaptedQueuePool,
}


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.async_engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self.sync_engine = None
        self.sync_session_factory = None
        self.redis_pool = None

    async def init_engine(self):
        """初始化数据库引擎"""
        if self.async_engine is not None:
            logger.warning("Database engine already initialized")
            return

        # 导入所有模型以确保SQLAlchemy关系正确初始化
        from app.domain.models import (  # noqa: F401
            User, Project, Task, Milestone, ProjectCostBudget, ProjectCostActual,
            ProjectRisk, ProjectDocument, ConversationSession, ConversationMessage,
            SkillDefinition, ProjectSkillSwitch, ApprovalWorkflow, AuditLog,
            KnowledgeDocument, RetrievalTrace, EventRecord, LLMUsageLog,
            UserProjectRole, GroupProjectBinding,
        )

        logger.info(
            "Initializing database connection pool",
            extra={
                "host": settings.database.host,
                "database": settings.database.name,
                "pool_size": settings.database.pool_size,
            }
        )

        self.async_engine = create_async_engine(
            settings.database.async_url,
            **DB_POOL_CONFIG
        )

        self.async_session_factory = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database engine initialized successfully")

    async def close_engine(self):
        """关闭数据库引擎"""
        if self.async_engine:
            await self.async_engine.dispose()
            self.async_engine = None
            self.async_session_factory = None
            logger.info("Database engine disposed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）"""
        if self.async_session_factory is None:
            raise RuntimeError("Database not initialized. Call init_engine() first.")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database transaction rollback: {str(e)}")
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_readonly_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取只读数据库会话"""
        if self.async_session_factory is None:
            raise RuntimeError("Database not initialized. Call init_engine() first.")

        async with self.async_session_factory() as session:
            try:
                # 设置只读事务
                await session.execute(text("SET TRANSACTION READ ONLY"))
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def check_connection(self) -> bool:
        """检查数据库连接状态"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.error("Database connection check failed", extra={"error": str(exc)})
            return False


# 全局数据库管理实例
db_manager = DatabaseManager()


# 保持向后兼容的函数
async def init_db() -> None:
    """Initialize database connection pool."""
    await db_manager.init_engine()


async def close_db() -> None:
    """Close database connection pool."""
    await db_manager.close_engine()


def get_async_session_factory():
    """
    Get async session factory.

    Returns the factory if initialized, None otherwise.
    """
    return db_manager.async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session (context manager).

    Yields:
        AsyncSession: Async database session

    Example:
        async with get_async_session() as session:
            result = await session.execute(query)
    """
    async with db_manager.get_session() as session:
        yield session


async def check_db_connection() -> bool:
    """Check database connection status."""
    return await db_manager.check_connection()


# Redis 管理功能
async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global _redis_pool

    if _redis_pool is not None:
        logger.warning("Redis already initialized")
        return

    try:
        import redis.asyncio as aioredis

        logger.info(
            "Initializing Redis connection pool",
            extra={
                "host": settings.redis.host,
                "port": settings.redis.port,
                "db": settings.redis.db,
            }
        )

        _redis_pool = aioredis.ConnectionPool.from_url(
            settings.redis.url,
            max_connections=settings.redis.pool_size,
            decode_responses=True,
        )

        logger.info("Redis connection pool initialized successfully")

    except ImportError:
        logger.warning("Redis package not installed, skipping initialization")


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool

    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def get_redis_client():
    """
    Get Redis client.

    Returns:
        redis.Redis: Redis client instance

    Raises:
        RuntimeError: Redis not initialized
    """
    if _redis_pool is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")

    import redis.asyncio as aioredis

    return aioredis.Redis(connection_pool=_redis_pool)


async def check_redis_connection() -> bool:
    """Check Redis connection status."""
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as exc:
        logger.error("Redis connection check failed", extra={"error": str(exc)})
        return False
