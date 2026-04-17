"""
PM Digital Employee - API Router
PM Digital Employee System - Global route registration

Feishu as the primary user interaction entrypoint.
"""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.lark_webhook import router as lark_webhook_router, internal_router as internal_router
from app.api.lark_callback import router as lark_callback_router

# Create main router
api_router = APIRouter()

# Register health check routes
api_router.include_router(health_router, tags=["Health"])

# Register Feishu webhook routes
api_router.include_router(lark_webhook_router, tags=["Feishu Webhook"])

# Register internal routes (for WebSocket callback)
api_router.include_router(internal_router, tags=["Internal"])

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


@api_v1_router.get("/users", tags=["Users"])
async def list_users(skip: int = 0, limit: int = 100):
    """列出用户."""
    return {
        "users": [],
        "skip": skip,
        "limit": limit,
        "total": 0,
    }


@api_v1_router.get("/users/{user_id}/projects", tags=["Users"])
async def get_user_projects(user_id: str):
    """获取用户参与的项目."""
    return {
        "user_id": user_id,
        "projects": [],
    }


@api_v1_router.get("/tasks", tags=["Tasks"])
async def list_tasks(project_id: str = None, status: str = None, skip: int = 0, limit: int = 100):
    """列出任务."""
    return {
        "tasks": [],
        "project_id": project_id,
        "status": status,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/risks", tags=["Risks"])
async def list_risks(project_id: str = None, level: str = None, skip: int = 0, limit: int = 100):
    """列出风险."""
    return {
        "risks": [],
        "project_id": project_id,
        "level": level,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/costs/budget", tags=["Costs"])
async def list_cost_budgets(project_id: str = None, skip: int = 0, limit: int = 100):
    """列出成本预算."""
    return {
        "budgets": [],
        "project_id": project_id,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/costs/actual", tags=["Costs"])
async def list_cost_actuals(project_id: str = None, skip: int = 0, limit: int = 100):
    """列出实际成本."""
    return {
        "actuals": [],
        "project_id": project_id,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/milestones", tags=["Milestones"])
async def list_milestones(project_id: str = None, skip: int = 0, limit: int = 100):
    """列出里程碑."""
    return {
        "milestones": [],
        "project_id": project_id,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/documents", tags=["Documents"])
async def list_documents(project_id: str = None, doc_type: str = None, skip: int = 0, limit: int = 100):
    """列出文档."""
    return {
        "documents": [],
        "project_id": project_id,
        "doc_type": doc_type,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/knowledge", tags=["Knowledge"])
async def list_knowledge(scope_type: str = None, skip: int = 0, limit: int = 100):
    """列出知识库文档."""
    return {
        "knowledge": [],
        "scope_type": scope_type,
        "skip": skip,
        "limit": limit,
    }


@api_v1_router.get("/llm/stats", tags=["LLM"])
async def get_llm_stats():
    """获取LLM使用统计."""
    from app.ai.llm_gateway import get_llm_gateway

    gateway = get_llm_gateway()
    summary = gateway.get_memory_stats_summary()
    return summary


@api_v1_router.get("/audit/logs", tags=["Audit"])
async def list_audit_logs():
    """列出审计日志."""
    return {"logs": []}


# 注册v1路由
api_router.include_router(api_v1_router)