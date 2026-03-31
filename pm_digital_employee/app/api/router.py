"""
PM Digital Employee - API Router Module
项目经理数字员工系统 - API路由注册模块

集中管理所有API路由注册，支持：
- 路由前缀
- 版本控制
- 模块化注册
- 依赖注入
"""

from fastapi import APIRouter, FastAPI

from app.api.health import router as health_router


def create_api_router() -> APIRouter:
    """
    创建主API路由器.

    Returns:
        APIRouter: 主路由器实例
    """
    router = APIRouter()

    # 注册健康检查路由（无前缀）
    router.include_router(health_router)

    return router


def setup_routers(app: FastAPI) -> None:
    """
    配置应用路由.

    将所有路由模块注册到FastAPI应用。

    Args:
        app: FastAPI应用实例
    """
    # 创建主路由器
    main_router = create_api_router()

    # 注册主路由器
    app.include_router(main_router)

    # 注册v1版本API（预留扩展）
    # app.include_router(v1_router, prefix="/api/v1")

    # 注册飞书Webhook路由（预留扩展）
    # app.include_router(lark_router, prefix="/lark")

    # 注册管理后台API（预留扩展）
    # app.include_router(admin_router, prefix="/api/admin")


def get_router_prefix(version: str = "v1") -> str:
    """
    获取API路由前缀.

    Args:
        version: API版本号

    Returns:
        str: 路由前缀
    """
    return f"/api/{version}"