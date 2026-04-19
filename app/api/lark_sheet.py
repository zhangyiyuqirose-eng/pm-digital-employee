"""
PM Digital Employee - Lark Sheet API
项目经理数字员工系统 - 飞书在线表格同步API接口

提供Webhook回调、表格绑定、同步状态查询和手动同步接口。

v1.2.0新增
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.lark.sheet_webhook import (
    SyncFrequency,
    SyncStatus,
    get_webhook_handler,
    get_sync_trigger,
    get_status_monitor,
    get_retry_manager,
)
from app.integrations.lark.signature import verify_lark_signature

logger = get_logger(__name__)

# 创建路由
router = APIRouter(prefix="/lark-sheet", tags=["Lark Sheet Sync"])


# ==================== 请求模型 ====================

class WebhookCallbackRequest(BaseModel):
    """飞书Webhook回调请求模型."""

    type: str = Field(..., description="事件类型")
    token: str = Field(..., description="飞书Token")
    ts: str = Field(..., description="时间戳")
    uuid: str = Field(..., description="事件UUID")
    event: Dict[str, Any] = Field(default_factory=dict, description="事件详情")


class SheetBindRequest(BaseModel):
    """表格绑定请求模型."""

    project_id: str = Field(..., description="项目ID")
    lark_sheet_token: str = Field(..., description="飞书表格Token")
    lark_sheet_id: str = Field(..., description="工作表ID")
    lark_sheet_name: Optional[str] = Field(None, description="工作表名称")
    module: str = Field(..., description="绑定模块（task/cost/risk/milestone等）")
    field_mappings: Dict[str, str] = Field(
        ...,
        description="字段映射配置，如{'A': 'name', 'B': 'code'}",
    )
    sync_mode: str = Field(
        default="bidirectional",
        description="同步模式（to_sheet/from_sheet/bidirectional）",
    )
    sync_frequency: str = Field(
        default="realtime",
        description="同步频率（realtime/5min/15min/1hour）",
    )
    data_range_start: Optional[str] = Field(None, description="数据起始行，如A2")
    data_range_end: Optional[str] = Field(None, description="数据结束范围")
    operator_id: Optional[str] = Field(None, description="操作人飞书用户ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")


class ManualSyncRequest(BaseModel):
    """手动同步请求模型."""

    direction: str = Field(
        default="bidirectional",
        description="同步方向（to_sheet/from_sheet/bidirectional）",
    )


# ==================== 响应模型 ====================

class WebhookCallbackResponse(BaseModel):
    """Webhook回调响应模型."""

    status: str = Field(..., description="处理状态")
    message: Optional[str] = Field(None, description="处理消息")


class BindingResponse(BaseModel):
    """绑定响应模型."""

    binding_id: str = Field(..., description="绑定配置ID")
    status: str = Field(..., description="绑定状态")
    message: Optional[str] = Field(None, description="状态消息")


class SyncStatusResponse(BaseModel):
    """同步状态响应模型."""

    binding_id: str = Field(..., description="绑定配置ID")
    sync_status: str = Field(..., description="同步状态")
    last_sync_at: Optional[str] = Field(None, description="最后同步时间")
    last_sync_status: Optional[str] = Field(None, description="最后同步状态")
    healthy: bool = Field(..., description="是否健康")
    health_details: Optional[Dict[str, Any]] = Field(None, description="健康检查详情")


class ManualSyncResponse(BaseModel):
    """手动同步响应模型."""

    binding_id: str = Field(..., description="绑定配置ID")
    task_id: str = Field(..., description="同步任务ID")
    status: str = Field(..., description="任务状态")
    triggered_at: str = Field(..., description="触发时间")


# ==================== API接口 ====================

@router.post(
    "/webhook",
    response_model=WebhookCallbackResponse,
    summary="飞书表格Webhook回调",
    description="接收飞书在线表格变更事件Webhook回调",
)
async def handle_webhook_callback(
    request: Request,
) -> WebhookCallbackResponse:
    """
    处理飞书表格Webhook回调.

    接收飞书在线表格数据变更事件，触发实时同步。

    Args:
        request: FastAPI请求对象

    Returns:
        WebhookCallbackResponse: 处理结果
    """
    logger.info("Received lark sheet webhook callback")

    # 验证签名
    body = await request.body()
    signature = request.headers.get("X-Lark-Signature", "")
    timestamp = request.headers.get("X-Lark-Timestamp", "")

    if settings.lark_verification_token:
        # 验证请求签名（生产环境必须验证）
        if not verify_lark_signature(
            body.decode("utf-8"),
            signature,
            timestamp,
            settings.lark_verification_token,
        ):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Signature verification failed")

    # 解析请求体
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook body")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 解析事件
    event_type = data.get("type", "")
    event_token = data.get("token", "")
    event_uuid = data.get("uuid", "")

    logger.info(f"Webhook event: type={event_type}, uuid={event_uuid}")

    # 根据事件类型处理
    if event_type == "url_verification":
        # URL验证回调，返回challenge
        challenge = data.get("challenge", "")
        return WebhookCallbackResponse(
            status="verified",
            message=challenge,  # 返回challenge用于验证
        )

    # 处理表格变更事件
    if event_type == "sheet_data_change" or event_type == "sheet_structure_change":
        # 获取绑定配置（根据表格token和sheet_id）
        event_data = data.get("event", {})
        sheet_token = event_data.get("sheet_token", "")
        sheet_id = event_data.get("sheet_id", "")

        # TODO: 从数据库获取绑定配置
        # binding_config = _get_binding_config(sheet_token, sheet_id)
        binding_config = {
            "id": str(uuid.uuid4()),
            "module": "task",
            "sync_mode": "bidirectional",
            "sync_frequency": "realtime",
        }

        # 调用Webhook处理器
        handler = get_webhook_handler()
        result = await handler.handle_webhook_event(data, binding_config)

        return WebhookCallbackResponse(
            status=result.get("status", "processed"),
            message=result.get("reason") or result.get("error"),
        )

    # 其他事件类型
    logger.warning(f"Unhandled webhook event type: {event_type}")
    return WebhookCallbackResponse(
        status="ignored",
        message=f"Event type {event_type} not handled",
    )


@router.post(
    "/bind",
    response_model=BindingResponse,
    summary="绑定飞书表格",
    description="创建飞书在线表格与系统模块的绑定配置",
)
async def bind_lark_sheet(
    request: SheetBindRequest,
) -> BindingResponse:
    """
    绑定飞书表格.

    创建飞书在线表格与系统模块的字段映射配置。

    Args:
        request: 绑定请求参数

    Returns:
        BindingResponse: 绑定结果
    """
    logger.info(
        f"Binding lark sheet: token={request.lark_sheet_token}, "
        f"sheet_id={request.lark_sheet_id}, module={request.module}"
    )

    # 验证同步频率
    valid_frequencies = [
        SyncFrequency.REALTIME,
        SyncFrequency.FIVE_MIN,
        SyncFrequency.FIFTEEN_MIN,
        SyncFrequency.ONE_HOUR,
    ]
    if request.sync_frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync_frequency: {request.sync_frequency}",
        )

    # 验证同步模式
    valid_modes = ["to_sheet", "from_sheet", "bidirectional"]
    if request.sync_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync_mode: {request.sync_mode}",
        )

    # TODO: 存储绑定配置到数据库
    # from app.repositories.lark_sheet_binding_repo import get_binding_repo
    # repo = get_binding_repo()
    # binding = repo.create(...)
    binding_id = str(uuid.uuid4())

    # 更新状态监控
    get_status_monitor().update_status(
        binding_id,
        SyncStatus.PENDING,
        {"message": "Binding created, waiting for first sync"},
    )

    logger.info(f"Binding created: id={binding_id}")

    return BindingResponse(
        binding_id=binding_id,
        status="created",
        message="飞书表格绑定配置创建成功",
    )


@router.get(
    "/status/{binding_id}",
    response_model=SyncStatusResponse,
    summary="查询同步状态",
    description="获取指定绑定配置的同步状态和健康信息",
)
async def get_sync_status(
    binding_id: str,
) -> SyncStatusResponse:
    """
    查询同步状态.

    获取飞书表格绑定配置的同步状态和健康检查结果。

    Args:
        binding_id: 绑定配置ID

    Returns:
        SyncStatusResponse: 同步状态信息
    """
    logger.info(f"Querying sync status for binding: {binding_id}")

    # 从状态监控获取状态
    monitor = get_status_monitor()
    status_info = monitor.get_status(binding_id)

    if not status_info:
        raise HTTPException(
            status_code=404,
            detail=f"Binding {binding_id} not found",
        )

    # 健康检查
    health_result = monitor.check_health(binding_id)

    return SyncStatusResponse(
        binding_id=binding_id,
        sync_status=status_info.get("status", SyncStatus.PENDING),
        last_sync_at=status_info.get("updated_at"),
        last_sync_status=status_info.get("details", {}).get("status"),
        healthy=health_result.get("healthy", False),
        health_details=health_result,
    )


@router.post(
    "/manual-sync/{binding_id}",
    response_model=ManualSyncResponse,
    summary="手动同步",
    description="触发指定绑定配置的手动同步",
)
async def trigger_manual_sync(
    binding_id: str,
    request: ManualSyncRequest = None,
) -> ManualSyncResponse:
    """
    触发手动同步.

    手动触发飞书表格与系统模块的数据同步。

    Args:
        binding_id: 绑定配置ID
        request: 同步请求参数

    Returns:
        ManualSyncResponse: 同步任务信息
    """
    logger.info(f"Triggering manual sync for binding: {binding_id}")

    # 验证绑定配置存在
    # TODO: 从数据库查询
    # binding = _get_binding_by_id(binding_id)
    # if not binding:
    #     raise HTTPException(status_code=404, detail=f"Binding {binding_id} not found")

    direction = request.direction if request else "bidirectional"

    # 触发同步
    trigger = get_sync_trigger()
    result = await trigger.trigger_manual_sync(binding_id, direction)

    # 异步执行同步任务
    from app.tasks.lark_sheet_sync_tasks import manual_sync_binding
    task = manual_sync_binding.apply_async(
        args=[binding_id, direction],
    )

    logger.info(f"Manual sync task created: task_id={task.id}")

    return ManualSyncResponse(
        binding_id=binding_id,
        task_id=task.id,
        status=SyncStatus.PENDING,
        triggered_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/bindings",
    summary="查询绑定配置列表",
    description="获取所有飞书表格绑定配置列表",
)
async def list_bindings(
    project_id: Optional[str] = None,
    module: Optional[str] = None,
    sync_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    查询绑定配置列表.

    根据条件筛选飞书表格绑定配置。

    Args:
        project_id: 项目ID筛选
        module: 模块筛选
        sync_enabled: 是否启用同步筛选

    Returns:
        Dict: 绑定配置列表
    """
    logger.info(
        f"Listing bindings: project_id={project_id}, "
        f"module={module}, sync_enabled={sync_enabled}"
    )

    # TODO: 从数据库查询
    # bindings = _query_bindings(project_id, module, sync_enabled)

    # 返回所有状态
    all_status = get_status_monitor().get_all_statuses()

    return {
        "bindings": [],
        "status_summary": all_status,
        "total": 0,
        "filters": {
            "project_id": project_id,
            "module": module,
            "sync_enabled": sync_enabled,
        },
    }


@router.delete(
    "/bindings/{binding_id}",
    summary="删除绑定配置",
    description="删除飞书表格绑定配置",
)
async def delete_binding(
    binding_id: str,
) -> Dict[str, Any]:
    """
    删除绑定配置.

    删除指定的飞书表格绑定配置，停止同步。

    Args:
        binding_id: 绑定配置ID

    Returns:
        Dict: 删除结果
    """
    logger.info(f"Deleting binding: {binding_id}")

    # TODO: 从数据库删除
    # _delete_binding(binding_id)

    # 清除状态监控
    get_status_monitor().update_status(
        binding_id,
        "deleted",
        {"deleted_at": datetime.now(timezone.utc).isoformat()},
    )

    return {
        "binding_id": binding_id,
        "status": "deleted",
        "message": "绑定配置已删除",
    }


@router.put(
    "/bindings/{binding_id}/toggle",
    summary="启用/禁用同步",
    description="切换绑定配置的同步启用状态",
)
async def toggle_sync(
    binding_id: str,
    enabled: bool = True,
) -> Dict[str, Any]:
    """
    切换同步启用状态.

    启用或禁用绑定配置的数据同步。

    Args:
        binding_id: 绑定配置ID
        enabled: 是否启用同步

    Returns:
        Dict: 更新结果
    """
    logger.info(f"Toggling sync for binding {binding_id}: enabled={enabled}")

    # TODO: 更新数据库
    # _update_binding_enabled(binding_id, enabled)

    # 更新状态
    status = "enabled" if enabled else "disabled"
    get_status_monitor().update_status(
        binding_id,
        SyncStatus.PENDING if enabled else status,
        {"sync_enabled": enabled, "updated_at": datetime.now(timezone.utc).isoformat()},
    )

    return {
        "binding_id": binding_id,
        "sync_enabled": enabled,
        "status": status,
        "message": f"同步已{'启用' if enabled else '禁用'}",
    }


# ==================== 辅助函数 ====================

def _get_binding_config(sheet_token: str, sheet_id: str) -> Optional[Dict[str, Any]]:
    """
    根据表格token和sheet_id获取绑定配置.

    Args:
        sheet_token: 飞书表格Token
        sheet_id: 工作表ID

    Returns:
        Dict: 绑定配置
    """
    # TODO: 实现数据库查询
    logger.debug(f"Querying binding config: token={sheet_token}, sheet_id={sheet_id}")
    return None