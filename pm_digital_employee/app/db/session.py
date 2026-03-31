"""
PM Digital Employee - Database Session Module
项目经理数字员工系统 - 数据库会话管理模块

实现：
- 异步数据库连接池管理
- 同步数据库连接（用于Alembic迁移）
- Redis连接池管理
- 会话工厂
- 上下文管理器
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 异步引擎和会话工厂
_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

# 同步引擎和会话工厂（用于Alembic迁移）
_sync_engine = None
_sync_session_factory = None

# Redis连接池
_redis_pool = None


async def init_db() -> None:
    """
    初始化数据库连接池.

    创建异步引擎和会话工厂。
    """
    global _async_engine, _async_session_factory

    if _async_engine is not None:
        logger.warning("Database already initialized")
        return

    logger.info(
        "Initializing database connection pool",
        host=settings.database.host,
        database=settings.database.name,
        pool_size=settings.database.pool_size,
    )

    # 创建异步引擎
    _async_engine = create_async_engine(
        settings.database.async_url,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_recycle=settings.database.pool_recycle,
        pool_timeout=settings.database.pool_timeout,
        echo=settings.is_development,
        future=True,
    )

    # 创建会话工厂
    _async_session_factory = async_sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info("Database connection pool initialized successfully")


async def close_db() -> None:
    """
    关闭数据库连接池.
    """
    global _async_engine, _async_session_factory

    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        logger.info("Database connection pool closed")


def get_sync_engine():
    """
    获取同步数据库引擎.

    用于Alembic迁移和同步操作。

    Returns:
        Engine: 同步SQLAlchemy引擎
    """
    global _sync_engine

    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.database.sync_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.is_development,
            future=True,
        )

    return _sync_engine


def get_sync_session_factory():
    """
    获取同步会话工厂.

    Returns:
        sessionmaker: 同步会话工厂
    """
    global _sync_session_factory

    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return _sync_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话（上下文管理器）.

    Yields:
        AsyncSession: 异步数据库会话

    Example:
        async with get_async_session() as session:
            result = await session.execute(query)
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    session = _async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_session() -> Generator[Session, None, None]:
    """
    获取同步数据库会话（上下文管理器）.

    用于Alembic迁移和同步操作。

    Yields:
        Session: 同步数据库会话
    """
    factory = get_sync_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def init_redis() -> None:
    """
    初始化Redis连接池.
    """
    global _redis_pool

    if _redis_pool is not None:
        logger.warning("Redis already initialized")
        return

    try:
        import redis.asyncio as aioredis

        logger.info(
            "Initializing Redis connection pool",
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
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
    """
    关闭Redis连接池.
    """
    global _redis_pool

    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


def get_redis_client():
    """
    获取Redis客户端.

    Returns:
        redis.Redis: Redis客户端实例

    Raises:
        RuntimeError: Redis未初始化
    """
    if _redis_pool is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")

    import redis.asyncio as aioredis

    return aioredis.Redis(connection_pool=_redis_pool)


@asynccontextmanager
async def get_redis() -> AsyncGenerator:
    """
    获取Redis客户端（上下文管理器）.

    Yields:
        redis.Redis: Redis客户端实例
    """
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.close()


async def check_db_connection() -> bool:
    """
    检查数据库连接状态.

    Returns:
        bool: 数据库是否可连接
    """
    try:
        async with get_async_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as exc:
        logger.error("Database connection check failed", error=str(exc))
        return False


async def check_redis_connection() -> bool:
    """
    检查Redis连接状态.

    Returns:
        bool: Redis是否可连接
    """
    try:
        async with get_redis() as client:
            await client.ping()
        return True
    except Exception as exc:
        logger.error("Redis connection check failed", error=str(exc))
        return False