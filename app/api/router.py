"""
PM Digital Employee - API Router
项目经理数字员工系统 - 全局路由注册
"""

from fastapi import APIRouter

from app.api.health import router as health_router

# 创建主路由
api_router = APIRouter()

# 注册健康检查路由
api_router.include_router(health_router, tags=["Health"])


# 飞书Webhook路由（简化版）
@api_router.post("/lark/webhook/message", tags=["Lark"])
async def receive_lark_message():
    """接收飞书消息."""
    return {"status": "ok"}


@api_router.post("/lark/callback/card", tags=["Lark"])
async def receive_lark_callback():
    """接收飞书回调."""
    return {"status": "ok"}


@api_router.post("/lark/url_verification", tags=["Lark"])
async def url_verification(request: dict):
    """飞书URL校验."""
    return {"challenge": request.get("challenge", "")}


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