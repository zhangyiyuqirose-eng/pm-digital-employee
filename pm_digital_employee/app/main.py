"""
PM Digital Employee - FastAPI Application Entry Point
项目经理数字员工系统 - FastAPI应用主入口

实现：
- 应用生命周期管理
- 路由注册
- 中间件配置
- 全局异常处理
- 启动/关闭钩子
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import setup_routers
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import setup_middlewares

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理.

    在应用启动前执行初始化操作，
    在应用关闭后执行清理操作。

    Args:
        app: FastAPI应用实例

    Yields:
        AsyncGenerator: 生命周期上下文
    """
    # ========== 启动阶段 ==========
    logger.info(
        "Application starting",
        app_name=settings.app.name,
        environment=settings.app.env,
        version=settings.app.version,
    )

    # 初始化数据库连接池
    try:
        from app.db.session import init_db

        await init_db()
        logger.info("Database connection pool initialized")
    except ImportError:
        logger.warning("Database module not found, skipping initialization")
    except Exception as exc:
        logger.error("Failed to initialize database", error=str(exc))
        if settings.is_production:
            raise

    # 初始化Redis连接池
    try:
        from app.db.session import init_redis

        await init_redis()
        logger.info("Redis connection pool initialized")
    except ImportError:
        logger.warning("Redis module not found, skipping initialization")
    except Exception as exc:
        logger.error("Failed to initialize Redis", error=str(exc))
        if settings.is_production:
            raise

    # 初始化Skill注册中心
    try:
        from app.orchestrator.skill_registry import SkillRegistry

        registry = SkillRegistry.get_instance()
        # 自动注册Skills
        from app.skills import register_skills

        register_skills(registry)
        logger.info("Skills registered", count=len(registry.list_all()))
    except ImportError:
        logger.warning("Skill modules not found, skipping skill registration")
    except Exception as exc:
        logger.warning("Failed to register skills", error=str(exc))

    logger.info(
        "Application started successfully",
        app_name=settings.app.name,
        host=settings.app.host,
        port=settings.app.port,
    )

    yield  # 应用运行中

    # ========== 关闭阶段 ==========
    logger.info("Application shutting down")

    # 关闭数据库连接池
    try:
        from app.db.session import close_db

        await close_db()
        logger.info("Database connection pool closed")
    except ImportError:
        pass
    except Exception as exc:
        logger.error("Error closing database", error=str(exc))

    # 关闭Redis连接池
    try:
        from app.db.session import close_redis

        await close_redis()
        logger.info("Redis connection pool closed")
    except ImportError:
        pass
    except Exception as exc:
        logger.error("Error closing Redis", error=str(exc))

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    创建并配置FastAPI应用实例.

    Returns:
        FastAPI: 配置完成的应用实例
    """
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.app.name,
        description="""
# 项目经理数字员工系统 (PM Digital Employee)

国有大型银行科技子公司项目管理部智能助理系统

## 核心功能

- 项目总览查询
- 项目周报生成
- WBS自动生成
- 任务进度更新
- 风险识别与预警
- 成本监控
- 项目制度规范答疑（RAG）
- 项目情况咨询
- 会议纪要生成
- 预立项/立项材料合规初审

## 技术架构

- **语言**: Python 3.11
- **Web框架**: FastAPI
- **数据库**: PostgreSQL + pgvector
- **缓存**: Redis
- **消息队列**: RabbitMQ
- **异步任务**: Celery

## 安全特性

- 项目级强隔离
- 全流程审计日志
- 权限感知RAG
- 提示词注入防护
        """,
        version=settings.app.version,
        docs_url="/docs" if settings.metrics.enable_health_details else None,
        redoc_url="/redoc" if settings.metrics.enable_health_details else None,
        openapi_url="/openapi.json" if settings.metrics.enable_health_details else None,
        lifespan=lifespan,
    )

    # 配置CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 配置自定义中间件
    setup_middlewares(app)

    # 配置路由
    setup_routers(app)

    logger.info(
        "FastAPI application created",
        title=app.title,
        version=app.version,
        docs_enabled=settings.metrics.enable_health_details,
    )

    return app


# 创建应用实例
app = create_application()


def main() -> None:
    """
    应用主入口函数.

    使用uvicorn启动应用。
    """
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        workers=settings.app.workers,
        reload=settings.is_development,
        log_level=settings.log.level.lower(),
        access_log=True,
        use_colors=True,
    )


if __name__ == "__main__":
    main()