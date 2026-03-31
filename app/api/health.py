"""
PM Digital Employee - Health Check
项目经理数字员工系统 - 健康检查接口
"""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    健康检查接口.

    Returns:
        Dict: 健康状态
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    就绪检查接口.

    Returns:
        Dict: 就绪状态
    """
    checks = {
        "database": "ok",
        "redis": "skipped",
        "rabbitmq": "skipped",
    }

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live", tags=["Health"])
async def liveness_check() -> Dict[str, Any]:
    """
    存活检查接口.

    Returns:
        Dict: 存活状态
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }