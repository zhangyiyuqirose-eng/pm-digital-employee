"""
PM Digital Employee - API Module
项目经理数字员工系统 - API模块
"""

from app.api.health import router as health_router
from app.api.router import api_router

__all__ = [
    "health_router",
    "api_router",
]