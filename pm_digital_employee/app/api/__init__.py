"""
PM Digital Employee - API Module
项目经理数字员工系统 - API模块初始化
"""

from app.api.health import router as health_router
from app.api.router import create_api_router, get_router_prefix, setup_routers

__all__ = [
    "setup_routers",
    "create_api_router",
    "get_router_prefix",
    "health_router",
]