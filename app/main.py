"""
PM Digital Employee - Main Application
项目经理数字员工系统 - FastAPI主入口
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.core.middleware import (
    TraceIDMiddleware,
    RequestLoggingMiddleware,
    ExceptionHandlerMiddleware,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理.
    """
    # 启动时执行
    logger.info(
        "Application starting",
        app_name=settings.app_name,
        environment=settings.app_env,
    )

    # 注册Skills
    try:
        from app.skills import register_all_skills
        register_all_skills()
        logger.info("Skills registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register skills: {e}")

    logger.info("Application started successfully")

    yield

    # 关闭时执行
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

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 添加自定义中间件
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TraceIDMiddleware)

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
        "lark_configured": bool(settings.lark_app_id),
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