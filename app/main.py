"""
PM Digital Employee - Main Application
项目经理数字员工系统 - FastAPI主入口

飞书作为唯一用户交互入口。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.core.middleware import (
    TraceIDMiddleware,
    RequestLoggingMiddleware,
    ExceptionHandlerMiddleware,
    RateLimitMiddleware,
    ConcurrentLimitMiddleware,
)
from app.core.rate_limiter import limiter

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理.
    """
    # 启动时执行
    logger.info(
        "Application starting",
        extra={
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "lark_configured": settings.lark_configured,
        }
    )

    # 注册Skills
    try:
        from app.skills import register_all_skills
        register_all_skills()
        logger.info("Skills registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register skills: {e}")

    # 初始化数据库
    try:
        from app.db.session import init_db
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # 启动飞书WebSocket长连接
    try:
        from app.integrations.lark.websocket import start_lark_websocket
        start_lark_websocket()
        logger.info("Lark WebSocket client started")
    except Exception as e:
        logger.warning(f"Failed to start Lark WebSocket: {e}")

    logger.info("Application started successfully")

    yield

    # 关闭时执行
    try:
        from app.integrations.lark.websocket import stop_lark_websocket
        stop_lark_websocket()
        logger.info("Lark WebSocket client stopped")
    except Exception as e:
        logger.warning(f"Failed to stop Lark WebSocket: {e}")

    try:
        from app.db.session import close_db
        await close_db()
        logger.info("Database closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database: {e}")

    logger.info("Application shutting down")
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    创建FastAPI应用实例.
    """
    app = FastAPI(
        title=settings.app_name,
        description="项目经理数字员工系统 - 基于飞书的项目管理智能助手",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=settings.cors_allow_origin_regex,
    )

    # 添加自定义中间件 - 按照处理顺序添加
    app.add_middleware(ConcurrentLimitMiddleware, max_concurrent=50)  # 并发控制
    app.add_middleware(RateLimitMiddleware, max_requests=60, time_window=60)  # 限流
    app.add_middleware(ExceptionHandlerMiddleware)  # 异常处理
    app.add_middleware(RequestLoggingMiddleware)    # 请求日志
    app.add_middleware(TraceIDMiddleware)           # 追踪ID

    # 注册路由
    app.include_router(api_router)

    return app


# 创建应用实例
app = create_application()


# 根路径
@app.get("/", tags=["Root"])
async def root():
    """根路径."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "lark_configured": settings.lark_configured,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=True,
        log_level="info",
    )