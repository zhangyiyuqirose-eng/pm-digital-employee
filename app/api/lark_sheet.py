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
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db_session
from app.core.logging import get_logger
from app.integrations.lark.signature import LarkSignatureVerifier
from app.services.lark_sheet_sync_service import LarkSheetSyncService
from app.services.sync_engine import SyncEngine, SyncStatus
from app.domain.enums import SyncMode, SyncFrequency

logger = get_logger(__name__)

# 创建路由
lark_sheet_router = APIRouter(prefix="/lark-sheet", tags=["Lark Sheet Sync"])


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
    status: str = Field(..., description="任务状态")
    triggered_at: str = Field(..., description="触发时间")
    result: Optional[Dict[str, Any]] = Field(None, description="同步结果")


# ==================== API接口 ====================

@lark_sheet_router.post(
    "/webhook",
    response_model=WebhookCallbackResponse,
    summary="飞书表格Webhook回调",
    description="接收飞书在线表格变更事件Webhook回调",
)
async def handle_webhook_callback(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> WebhookCallbackResponse:
    """
    处理飞书表格Webhook回调.

    接收飞书在线表格数据变更事件，触发实时同步。

    Args:
        request: FastAPI请求对象
        session: 数据库会话

    Returns:
        WebhookCallbackResponse: 处理结果
    """
    logger.info("Received lark sheet webhook callback")

    # 验证签名
    body = await request.body()
    signature = request.headers.get("X-Lark-Signature", "")
    timestamp = request.headers.get("X-Lark-Timestamp", "")
    nonce = request.headers.get("X-Lark-Nonce", "")

    if settings.lark_encrypt_key:
        # 验证请求签名（生产环境必须验证）
        verifier = LarkSignatureVerifier()
        if not verifier.verify_signature(
            signature=signature,
            timestamp=timestamp,
            nonce=nonce,
            body=body.decode("utf-8"),
            encrypt_key=settings.lark_encrypt_key,
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
    if event_type in ["sheet_data_change", "sheet_structure_change"]:
        # 使用LarkSheetSyncService处理webhook
        service = LarkSheetSyncService(session)
        event_data = data.get("event", {})

        # 补充事件信息
        event_data["type"] = event_type
        event_data["spreadsheet_token"] = event_data.get("sheet_token", "")
        event_data["sheet_id"] = event_data.get("sheet_id", "")

        result = await service.handle_sheet_webhook(event_data)

        return WebhookCallbackResponse(
            status=result.get("status", "processed"),
            message=result.get("message"),
        )

    # 其他事件类型
    logger.warning(f"Unhandled webhook event type: {event_type}")
    return WebhookCallbackResponse(
        status="ignored",
        message=f"Event type {event_type} not handled",
    )


@lark_sheet_router.post(
    "/bind",
    response_model=BindingResponse,
    summary="绑定飞书表格",
    description="创建飞书在线表格与系统模块的绑定配置",
)
async def bind_lark_sheet(
    request: SheetBindRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BindingResponse:
    """
    绑定飞书表格.

    创建飞书在线表格与系统模块的字段映射配置。

    Args:
        request: 绑定请求参数
        session: 数据库会话

    Returns:
        BindingResponse: 绑定结果
    """
    logger.info(
        f"Binding lark sheet: token={request.lark_sheet_token}, "
        f"sheet_id={request.lark_sheet_id}, module={request.module}"
    )

    # 验证同步频率
    valid_frequencies = [
        SyncFrequency.REALTIME.value,
        SyncFrequency.FIVE_MINUTES.value,
        SyncFrequency.FIFTEEN_MINUTES.value,
        SyncFrequency.ONE_HOUR.value,
    ]
    if request.sync_frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync_frequency: {request.sync_frequency}",
        )

    # 验证同步模式
    valid_modes = [
        SyncMode.TO_SHEET.value,
        SyncMode.FROM_SHEET.value,
        SyncMode.BIDIRECTIONAL.value,
    ]
    if request.sync_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync_mode: {request.sync_mode}",
        )

    try:
        # 使用SyncEngine创建绑定
        engine = SyncEngine(session)

        project_uuid = uuid.UUID(request.project_id)

        binding = await engine.create_binding(
            project_id=project_uuid,
            lark_sheet_token=request.lark_sheet_token,
            lark_sheet_id=request.lark_sheet_id,
            module=request.module,
            field_mappings=json.dumps(request.field_mappings),
            sync_mode=request.sync_mode,
            sync_frequency=request.sync_frequency,
            data_range_start=request.data_range_start,
            data_range_end=request.data_range_end,
        )

        logger.info(f"Binding created: id={str(binding.id)}")

        return BindingResponse(
            binding_id=str(binding.id),
            status="created",
            message="飞书表格绑定配置创建成功",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create binding: {e}")
        raise HTTPException(status_code=500, detail=f"绑定创建失败: {str(e)}")


@lark_sheet_router.get(
    "/status/{binding_id}",
    response_model=SyncStatusResponse,
    summary="查询同步状态",
    description="获取指定绑定配置的同步状态和健康信息",
)
async def get_sync_status(
    binding_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> SyncStatusResponse:
    """
    查询同步状态.

    获取飞书表格绑定配置的同步状态和健康检查结果。

    Args:
        binding_id: 绑定配置ID
        session: 数据库会话

    Returns:
        SyncStatusResponse: 同步状态信息
    """
    logger.info(f"Querying sync status for binding: {binding_id}")

    try:
        binding_uuid = uuid.UUID(binding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="绑定ID格式错误")

    try:
        engine = SyncEngine(session)
        binding = await engine.get_lark_sheet_binding(binding_uuid)

        if not binding:
            raise HTTPException(
                status_code=404,
                detail=f"Binding {binding_id} not found",
            )

        # 健康检查（简化实现）
        healthy = True
        health_details = {
            "sync_enabled": binding.sync_enabled,
            "last_sync_status": binding.last_sync_status,
        }

        if not binding.sync_enabled:
            healthy = False
            health_details["reason"] = "同步已禁用"

        return SyncStatusResponse(
            binding_id=binding_id,
            sync_status=binding.last_sync_status or SyncStatus.PENDING.value,
            last_sync_at=str(binding.last_sync_at) if binding.last_sync_at else None,
            last_sync_status=binding.last_sync_status,
            healthy=healthy,
            health_details=health_details,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@lark_sheet_router.post(
    "/manual-sync/{binding_id}",
    response_model=ManualSyncResponse,
    summary="手动同步",
    description="触发指定绑定配置的手动同步",
)
async def trigger_manual_sync(
    binding_id: str,
    request: ManualSyncRequest = None,
    session: AsyncSession = Depends(get_db_session),
) -> ManualSyncResponse:
    """
    触发手动同步.

    手动触发飞书表格与系统模块的数据同步。

    Args:
        binding_id: 绑定配置ID
        request: 同步请求参数
        session: 数据库会话

    Returns:
        ManualSyncResponse: 同步任务信息
    """
    logger.info(f"Triggering manual sync for binding: {binding_id}")

    try:
        binding_uuid = uuid.UUID(binding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="绑定ID格式错误")

    try:
        service = LarkSheetSyncService(session)
        direction = request.direction if request else "bidirectional"

        # 根据方向执行同步
        if direction in ["from_sheet", "bidirectional"]:
            result = await service.sync_from_sheet(binding_uuid)
        elif direction == "to_sheet":
            result = await service.sync_to_sheet(binding_uuid)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid direction: {direction}",
            )

        logger.info(f"Manual sync completed: binding_id={binding_id}, result={result}")

        return ManualSyncResponse(
            binding_id=binding_id,
            status=result.get("status", "completed"),
            triggered_at=datetime.now(timezone.utc).isoformat(),
            result=result,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger manual sync: {e}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


@lark_sheet_router.get(
    "/bindings",
    summary="查询绑定配置列表",
    description="获取所有飞书表格绑定配置列表",
)
async def list_bindings(
    project_id: Optional[str] = None,
    module: Optional[str] = None,
    sync_enabled: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    查询绑定配置列表.

    根据条件筛选飞书表格绑定配置。

    Args:
        project_id: 项目ID筛选
        module: 模块筛选
        sync_enabled: 是否启用同步筛选
        session: 数据库会话

    Returns:
        Dict: 绑定配置列表
    """
    logger.info(
        f"Listing bindings: project_id={project_id}, "
        f"module={module}, sync_enabled={sync_enabled}"
    )

    try:
        engine = SyncEngine(session)

        project_uuid = None
        if project_id:
            project_uuid = uuid.UUID(project_id)

        bindings = await engine.get_active_bindings(
            project_id=project_uuid,
            module=module,
            sync_enabled=sync_enabled,
        )

        binding_list = []
        for binding in bindings:
            binding_list.append({
                "id": str(binding.id),
                "project_id": str(binding.project_id),
                "lark_sheet_token": binding.lark_sheet_token,
                "lark_sheet_id": binding.lark_sheet_id,
                "module": binding.module,
                "sync_mode": binding.sync_mode,
                "sync_frequency": binding.sync_frequency,
                "sync_enabled": binding.sync_enabled,
                "last_sync_at": str(binding.last_sync_at) if binding.last_sync_at else None,
                "last_sync_status": binding.last_sync_status,
            })

        return {
            "bindings": binding_list,
            "total": len(binding_list),
            "filters": {
                "project_id": project_id,
                "module": module,
                "sync_enabled": sync_enabled,
            },
        }

    except Exception as e:
        logger.error(f"Failed to list bindings: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@lark_sheet_router.delete(
    "/bindings/{binding_id}",
    summary="删除绑定配置",
    description="删除飞书表格绑定配置",
)
async def delete_binding(
    binding_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    删除绑定配置.

    删除指定的飞书表格绑定配置，停止同步。

    Args:
        binding_id: 绑定配置ID
        session: 数据库会话

    Returns:
        Dict: 删除结果
    """
    logger.info(f"Deleting binding: {binding_id}")

    try:
        binding_uuid = uuid.UUID(binding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="绑定ID格式错误")

    try:
        engine = SyncEngine(session)
        success = await engine.delete_binding(binding_uuid)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Binding {binding_id} not found",
            )

        return {
            "binding_id": binding_id,
            "status": "deleted",
            "message": "绑定配置已删除",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete binding: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@lark_sheet_router.put(
    "/bindings/{binding_id}/toggle",
    summary="启用/禁用同步",
    description="切换绑定配置的同步启用状态",
)
async def toggle_sync(
    binding_id: str,
    enabled: bool = True,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    切换同步启用状态.

    启用或禁用绑定配置的数据同步。

    Args:
        binding_id: 绑定配置ID
        enabled: 是否启用同步
        session: 数据库会话

    Returns:
        Dict: 更新结果
    """
    logger.info(f"Toggling sync for binding {binding_id}: enabled={enabled}")

    try:
        binding_uuid = uuid.UUID(binding_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="绑定ID格式错误")

    try:
        engine = SyncEngine(session)
        binding = await engine.toggle_binding_sync(binding_uuid, enabled)

        if not binding:
            raise HTTPException(
                status_code=404,
                detail=f"Binding {binding_id} not found",
            )

        status = "enabled" if enabled else "disabled"

        return {
            "binding_id": binding_id,
            "sync_enabled": enabled,
            "status": status,
            "message": f"同步已{'启用' if enabled else '禁用'}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle sync: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")