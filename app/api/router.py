"""
PM Digital Employee - API Router
PM Digital Employee System - Global route registration

Feishu as the primary user interaction entrypoint.
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.lark_webhook import router as lark_webhook_router
from app.api.lark_callback import router as lark_callback_router

# Create main router
api_router = APIRouter()

# Register health check routes
api_router.include_router(health_router, tags=["Health"])

# Register Feishu webhook routes
api_router.include_router(lark_webhook_router, tags=["Feishu Webhook"])

# Register Feishu callback routes
api_router.include_router(lark_callback_router, tags=["Feishu Callback"])


# API v1路由
api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/projects", tags=["Projects"])
async def list_projects():
    """列出项目."""
    return {"projects": []}


@api_v1_router.get("/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str):
    """获取项目详情."""
    return {"project_id": project_id, "name": "测试项目", "status": "进行中"}


@api_v1_router.get("/skills", tags=["Skills"])
async def list_skills():
    """列出可用Skills."""
    from app.orchestrator.skill_registry import get_skill_registry

    registry = get_skill_registry()
    skills = registry.list_all_skills()

    return {
        "skills": [
            {
                "name": s.skill_name,
                "display_name": s.display_name,
                "description": s.description,
            }
            for s in skills
        ],
    }


@api_v1_router.get("/audit/logs", tags=["Audit"])
async def list_audit_logs():
    """列出审计日志."""
    return {"logs": []}


# 注册v1路由
api_router.include_router(api_v1_router)