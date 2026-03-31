"""
PM Digital Employee - Alembic Environment Configuration
项目经理数字员工系统 - Alembic迁移环境配置

配置Alembic迁移工具的运行环境，支持：
- 同步和异步迁移
- 自动生成迁移脚本
- 环境变量配置
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.orm import declarative_base

# Alembic配置对象
config = context.config

# 解析日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入所有模型以便自动生成迁移
# 注意：这里需要导入所有模型类
from app.domain.base import Base  # noqa

# 添加模型的元数据
target_metadata = Base.metadata


def get_url() -> str:
    """
    从环境变量获取数据库连接URL.

    Returns:
        str: 数据库连接URL
    """
    import os

    # 优先使用alembic.ini中的配置
    url = config.get_main_option("sqlalchemy.url")
    if url and not url.startswith("%"):
        return url

    # 从环境变量读取
    user = os.getenv("POSTGRES_USER", "pm_user")
    password = os.getenv("POSTGRES_PASSWORD", "pm_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "pm_digital_employee")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def run_migrations_offline() -> None:
    """
    在'离线'模式下运行迁移.

    此模式不连接数据库，只生成SQL脚本。
    适用于：
    - 生成迁移脚本
    - 代码审查
    - 手动执行迁移
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 比较类型和服务器默认值
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    执行迁移.

    Args:
        connection: 数据库连接
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 比较类型和服务器默认值
        compare_type=True,
        compare_server_default=True,
        # 事务模式
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    在'在线'模式下运行异步迁移.

    此模式连接数据库执行迁移。
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在'在线'模式下运行迁移.

    此模式连接数据库执行迁移。
    支持同步和异步两种方式。
    """
    # 使用异步引擎
    asyncio.run(run_async_migrations())


# 根据上下文选择运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()