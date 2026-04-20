"""
PM Digital Employee - Alembic Environment Configuration
数据库迁移环境配置

支持异步SQLAlchemy和自动模型发现。
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, engine_from_config
from sqlalchemy.engine import Connection

from alembic import context

# 导入配置和所有模型
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.domain.base import Base
from app.domain.models import *  # 导入所有模型

# Alembic配置
config = context.config

# 从环境变量或settings获取数据库URL
# Alembic需要同步驱动，将asyncpg替换为普通psycopg2或使用postgresql://
db_url = os.environ.get("DATABASE_URL_SYNC", "")
if not db_url:
    db_url = str(settings.database.url)
if "asyncpg" in db_url:
    # 替换asyncpg为同步驱动用于迁移
    db_url = db_url.replace("+asyncpg", "")
# 如果是容器内postgres服务名，替换为宿主机可访问的地址
if "postgres:5432" in db_url:
    db_url = db_url.replace("postgres:5432", "localhost:15432")
config.set_main_option("sqlalchemy.url", db_url)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 元数据对象，用于autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移.

    直接生成SQL脚本，不需要数据库连接。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    异步模式运行迁移.

    使用异步引擎连接数据库。
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移.

    连接数据库执行迁移（同步模式）。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()