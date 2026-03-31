"""
PM Digital Employee - Database Initialization Script
项目经理数字员工系统 - 数据库初始化脚本

初始化数据库、创建扩展、执行迁移。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

from app.core.config import settings
from app.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


def init_pgvector_extension() -> None:
    """初始化pgvector扩展."""
    logger.info("Initializing pgvector extension...")

    # 创建同步引擎
    engine = create_engine(settings.database.sync_url)

    with engine.connect() as conn:
        # 创建pgvector扩展
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    logger.info("pgvector extension initialized successfully")


def init_database() -> None:
    """初始化数据库."""
    logger.info(
        "Initializing database",
        host=settings.database.host,
        database=settings.database.name,
    )

    try:
        # 初始化pgvector扩展
        init_pgvector_extension()

        # 运行Alembic迁移
        logger.info("Running Alembic migrations...")
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        logger.info("Database initialization completed successfully")

    except Exception as exc:
        logger.error("Database initialization failed", error=str(exc))
        raise


async def create_initial_data() -> None:
    """创建初始数据."""
    logger.info("Creating initial data...")

    from app.db.session import init_db, get_async_session

    await init_db()

    async with get_async_session() as session:
        # 创建默认Skill定义
        from app.domain.models.skill_definition import SkillDefinition

        skills_data = [
            {
                "skill_name": "project_overview",
                "display_name": "项目总览查询",
                "description": "查询项目整体进度、任务、风险、成本等核心指标",
                "domain": "project",
                "manifest": '{"skill_name": "project_overview", "display_name": "项目总览查询", "description": "查询项目整体进度、任务、风险、成本等核心指标", "version": "1.0.0", "domain": "project", "allowed_roles": ["project_manager", "pm", "tech_lead", "member"], "required_permissions": [{"resource": "project", "action": "read"}]}',
            },
            {
                "skill_name": "generate_weekly_report",
                "display_name": "项目周报生成",
                "description": "自动生成项目周报，汇总本周任务完成情况、风险、成本等",
                "domain": "report",
                "manifest": '{"skill_name": "generate_weekly_report", "display_name": "项目周报生成", "description": "自动生成项目周报，汇总本周任务完成情况、风险、成本等", "version": "1.0.0", "domain": "report", "allowed_roles": ["project_manager", "pm", "tech_lead"], "required_permissions": [{"resource": "report", "action": "execute"}, {"resource": "project", "action": "read"}], "supports_async": true}',
            },
        ]

        for skill_data in skills_data:
            existing = await session.execute(
                select(SkillDefinition).where(SkillDefinition.skill_name == skill_data["skill_name"])
            )
            if existing.scalar_one_or_none() is None:
                skill = SkillDefinition(**skill_data)
                session.add(skill)

        await session.commit()
        logger.info("Initial data created successfully")


def main() -> None:
    """主函数."""
    setup_logging()
    logger.info("Starting database initialization...")

    # 同步初始化
    init_database()

    # 异步创建初始数据
    asyncio.run(create_initial_data())

    logger.info("Database initialization completed")


if __name__ == "__main__":
    main()