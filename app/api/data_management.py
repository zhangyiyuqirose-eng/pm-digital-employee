"""
PM Digital Employee - Data Management API
项目经理数字员工系统 - 数据管理API端点

提供项目、任务、风险、成本、里程碑的CRUD操作。
"""

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime

from app.core.dependencies import get_db_session
from app.core.logging import get_logger, set_trace_id
from app.domain.enums import ProjectStatus, TaskStatus, RiskLevel
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.services.risk_service import RiskService
from app.services.cost_service import CostService
from app.services.milestone_service import MilestoneService

logger = get_logger(__name__)

# 创建管理API路由
data_router = APIRouter(prefix="/api/v1/data", tags=["Data Management"])


# ==================== 项目管理 ====================

@data_router.post("/projects")
async def create_project(
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    创建项目.

    Args:
        request: 请求数据
        session: 数据库会话

    Returns:
        Dict: 创建结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Creating project", trace_id=trace_id, name=data.get("name"))

    service = ProjectService(session)
    project = await service.create_project(
        name=data.get("name"),
        code=data.get("code"),
        description=data.get("description"),
        project_type=data.get("project_type", "研发项目"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        total_budget=data.get("total_budget"),
        pm_id=data.get("pm_id"),
        department_id=data.get("department_id"),
    )

    return {
        "code": 0,
        "msg": "项目创建成功",
        "data": {
            "project_id": str(project.id),
            "name": project.name,
            "code": project.code,
            "status": project.status,
        },
    }


@data_router.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    更新项目.

    Args:
        project_id: 项目ID
        request: 请求数据

    Returns:
        Dict: 更新结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Updating project", trace_id=trace_id, project_id=project_id)

    service = ProjectService(session)
    project = await service.update_project(
        project_id=uuid.UUID(project_id),
        **data,
    )

    return {
        "code": 0,
        "msg": "项目更新成功",
        "data": {
            "project_id": str(project.id),
            "name": project.name,
        },
    }


# ==================== 任务管理 ====================

@data_router.post("/projects/{project_id}/tasks")
async def create_task(
    project_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    创建任务.

    Args:
        project_id: 项目ID
        request: 请求数据

    Returns:
        Dict: 创建结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Creating task", trace_id=trace_id, project_id=project_id, name=data.get("name"))

    # 日期转换
    start_date_obj = None
    end_date_obj = None
    if data.get("start_date"):
        start_date_obj = datetime.strptime(data.get("start_date"), '%Y-%m-%d').date()
    if data.get("end_date"):
        end_date_obj = datetime.strptime(data.get("end_date"), '%Y-%m-%d').date()

    # priority转换（整数转字符串）
    priority_val = data.get("priority", 2)
    if isinstance(priority_val, int):
        priority_map = {1: "high", 2: "medium", 3: "low", 4: "critical"}
        priority_val = priority_map.get(priority_val, "medium")

    service = TaskService(session)
    task = await service.create_task(
        project_id=uuid.UUID(project_id),
        name=data.get("name"),
        description=data.get("description"),
        assignee_id=data.get("assignee_id"),
        start_date=start_date_obj,
        end_date=end_date_obj,
        priority=priority_val,
        status=data.get("status", "未开始"),
    )

    return {
        "code": 0,
        "msg": "任务创建成功",
        "data": {
            "task_id": str(task.id),
            "name": task.name,
            "status": task.status,
        },
    }


@data_router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    更新任务.

    Args:
        task_id: 任务ID
        request: 请求数据

    Returns:
        Dict: 更新结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Updating task", trace_id=trace_id, task_id=task_id)

    service = TaskService(session)
    task = await service.update_task(
        task_id=uuid.UUID(task_id),
        **data,
    )

    return {
        "code": 0,
        "msg": "任务更新成功",
        "data": {
            "task_id": str(task.id),
            "name": task.name,
            "status": task.status,
        },
    }


# ==================== 风险管理 ====================

@data_router.post("/projects/{project_id}/risks")
async def create_risk(
    project_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    创建风险.

    Args:
        project_id: 项目ID
        request: 请求数据

    Returns:
        Dict: 创建结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Creating risk", trace_id=trace_id, project_id=project_id, name=data.get("name"))

    service = RiskService(session)
    risk = await service.create_risk(
        project_id=uuid.UUID(project_id),
        title=data.get("name"),  # name映射到title
        description=data.get("description"),
        level=data.get("level", "中"),
        category=data.get("category", "schedule"),  # 默认category为schedule
        mitigation_plan=data.get("mitigation_plan"),
        owner_id=data.get("owner_id"),
    )

    return {
        "code": 0,
        "msg": "风险登记成功",
        "data": {
            "risk_id": str(risk.id),
            "name": risk.title,  # title映射到name
            "level": risk.level,
        },
    }


# ==================== 成本管理 ====================

@data_router.post("/projects/{project_id}/costs")
async def create_cost(
    project_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    创建成本记录.

    Args:
        project_id: 项目ID
        request: 请求数据

    Returns:
        Dict: 创建结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    cost_type = data.get("cost_type", "budget")  # budget or actual
    logger.info("Creating cost", trace_id=trace_id, project_id=project_id, cost_type=cost_type)

    # 日期转换
    expense_date_obj = None
    if data.get("occurred_date"):
        expense_date_obj = datetime.strptime(data.get("occurred_date"), '%Y-%m-%d').date()

    service = CostService(session)

    if cost_type == "budget":
        cost = await service.create_budget(
            project_id=uuid.UUID(project_id),
            category=data.get("category"),
            amount=data.get("amount"),
            description=data.get("description"),
        )
    else:
        cost = await service.create_actual(
            project_id=uuid.UUID(project_id),
            category=data.get("category"),
            amount=data.get("amount"),
            expense_date=expense_date_obj,  # occurred_date映射到expense_date
            description=data.get("description"),
        )

    return {
        "code": 0,
        "msg": "成本录入成功",
        "data": {
            "cost_id": str(cost.id),
            "category": cost.category,
            "amount": float(cost.amount),
        },
    }


# ==================== 里程碑管理 ====================

@data_router.post("/projects/{project_id}/milestones")
async def create_milestone(
    project_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    创建里程碑.

    Args:
        project_id: 项目ID
        request: 请求数据

    Returns:
        Dict: 创建结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Creating milestone", trace_id=trace_id, project_id=project_id, name=data.get("name"))

    # 日期转换
    due_date_obj = None
    if data.get("planned_date"):
        due_date_obj = datetime.strptime(data.get("planned_date"), '%Y-%m-%d').date()

    service = MilestoneService(session)
    milestone = await service.create_milestone(
        project_id=uuid.UUID(project_id),
        name=data.get("name"),
        due_date=due_date_obj,  # planned_date映射到due_date
        description=data.get("description"),
        status=data.get("status", "未完成"),
    )

    return {
        "code": 0,
        "msg": "里程碑创建成功",
        "data": {
            "milestone_id": str(milestone.id),
            "name": milestone.name,
            "status": milestone.status,
        },
    }


@data_router.put("/milestones/{milestone_id}")
async def update_milestone(
    milestone_id: str,
    request: Request,
    session=Depends(get_db_session),
) -> Dict[str, Any]:
    """
    更新里程碑.

    Args:
        milestone_id: 里程碑ID
        request: 请求数据

    Returns:
        Dict: 更新结果
    """
    data = await request.json()
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)

    logger.info("Updating milestone", trace_id=trace_id, milestone_id=milestone_id)

    service = MilestoneService(session)
    milestone = await service.update_milestone(
        milestone_id=uuid.UUID(milestone_id),
        **data,
    )

    return {
        "code": 0,
        "msg": "里程碑更新成功",
        "data": {
            "milestone_id": str(milestone.id),
            "name": milestone.name,
            "status": milestone.status,
        },
    }