"""
PM Digital Employee - Lark Card Callback
项目经理数字员工系统 - 飞书卡片回调处理接口

处理飞书交互式卡片的按钮点击、表单提交等用户交互。
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request

from app.core.config import settings
from app.core.logging import get_logger, set_trace_id
from app.integrations.lark.schemas import LarkCardCallback
from app.integrations.lark.service import get_lark_service
from app.integrations.lark.signature import verify_lark_request, LarkSignatureVerifier
from app.services.idempotency_service import get_card_callback_idempotency_service

logger = get_logger(__name__)

router = APIRouter(prefix="/lark/callback", tags=["Lark Callback"])


async def verify_request_signature(
    request: Request,
    x_lark_request_timestamp: str = Header(None, alias="X-Lark-Request-Timestamp"),
    x_lark_request_nonce: str = Header(None, alias="X-Lark-Request-Nonce"),
    x_lark_signature: str = Header(None, alias="X-Lark-Signature"),
) -> bool:
    """
    验证飞书请求签名.

    Args:
        request: FastAPI请求对象
        x_lark_request_timestamp: 时间戳Header
        x_lark_request_nonce: 随机数Header
        x_lark_signature: 签名Header

    Returns:
        bool: 验证是否通过
    """
    if not settings.lark.verify_signature:
        return True

    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        verify_lark_request(
            timestamp=x_lark_request_timestamp or "",
            nonce=x_lark_request_nonce or "",
            body=body_str,
            signature=x_lark_signature or "",
        )
        return True
    except Exception as e:
        logger.warning("Lark signature verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Signature verification failed")


@router.post("/card")
async def receive_card_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_request_signature),
) -> Dict[str, Any]:
    """
    接收飞书卡片回调.

    用户在交互式卡片上点击按钮、提交表单后，飞书推送回调到此接口。

    Args:
        request: FastAPI请求对象
        background_tasks: 后台任务

    Returns:
        Dict: 响应结果（通常需要返回新卡片内容）
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        # 解析回调请求
        callback_data = json.loads(body_str)

        # 处理URL验证
        if callback_data.get("type") == "url_verification":
            logger.info("Lark card callback URL verification")
            return {
                "challenge": LarkSignatureVerifier.verify_url(
                    callback_data.get("challenge", ""),
                ),
            }

        # 解析卡片回调
        callback = LarkCardCallback.model_validate(callback_data)

        # 设置trace_id
        trace_id = f"card:{callback.open_message_id}:{callback.open_id}"
        set_trace_id(trace_id)

        logger.info(
            "Lark card callback received",
            open_message_id=callback.open_message_id,
            open_chat_id=callback.open_chat_id,
            open_id=callback.open_id,
            action_tag=callback.action.tag if callback.action else None,
        )

        # 获取动作值
        action = callback.action
        if not action:
            logger.warning("No action in card callback")
            return {"code": 0, "msg": "no action"}

        action_value = action.value

        # 幂等检查
        idempotency_service = get_card_callback_idempotency_service()
        if not await idempotency_service.check_callback(
            callback.open_message_id,
            action_value,
        ):
            logger.info(
                "Card callback already processed",
                open_message_id=callback.open_message_id,
            )
            # 返回已处理提示卡片
            return _build_already_processed_response()

        # 获取用户信息
        user_open_id = callback.open_id
        chat_id = callback.open_chat_id

        # 异步处理回调
        background_tasks.add_task(
            _process_card_callback_async,
            callback,
            trace_id,
        )

        # 返回处理中提示卡片（飞书期望立即返回新卡片内容）
        return _build_processing_response()

    except json.JSONDecodeError:
        logger.error("Failed to parse card callback body")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error("Failed to handle card callback", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")


async def _process_card_callback_async(
    callback: LarkCardCallback,
    trace_id: str,
) -> None:
    """
    异步处理卡片回调.

    Args:
        callback: 卡片回调对象
        trace_id: 追踪ID
    """
    set_trace_id(trace_id)

    idempotency_service = get_card_callback_idempotency_service()

    try:
        action = callback.action
        action_value = action.value if action else {}

        logger.info(
            "Processing card callback async",
            open_message_id=callback.open_message_id,
            action_value=action_value,
        )

        # 获取动作类型
        action_type = action_value.get("action", "")

        # 根据动作类型分发处理
        if action_type == "confirm":
            # 确认执行Skill
            result = await _handle_confirm_action(callback, action_value)
        elif action_type == "cancel":
            # 取消操作
            result = await _handle_cancel_action(callback)
        elif action_type == "select_project":
            # 选择项目
            result = await _handle_select_project_action(callback, action_value)
        elif action_type == "update_task":
            # 更新任务
            result = await _handle_update_task_action(callback, action_value)
        elif action_type == "acknowledge_risk":
            # 确认风险
            result = await _handle_acknowledge_risk_action(callback, action_value)
        elif action_type == "approve":
            # 审批通过
            result = await _handle_approve_action(callback, action_value)
        elif action_type == "reject":
            # 审批拒绝
            result = await _handle_reject_action(callback, action_value)
        elif action_type == "retry":
            # 重试操作
            result = await _handle_retry_action(callback, action_value)
        else:
            # 未知的动作类型
            logger.warning(
                "Unknown action type in card callback",
                action_type=action_type,
            )
            result = {"success": False, "error": "未知操作类型"}

        # 标记处理完成
        await idempotency_service.mark_callback_completed(
            callback.open_message_id,
            action_value,
            result.get("card_id"),
        )

        # 发送结果卡片
        if result.get("success"):
            await _send_success_card(callback, result)
        else:
            await _send_error_card(callback, result.get("error", "处理失败"))

        logger.info(
            "Card callback processed",
            open_message_id=callback.open_message_id,
            success=result.get("success"),
        )

    except Exception as e:
        logger.error(
            "Failed to process card callback async",
            open_message_id=callback.open_message_id,
            error=str(e),
        )

        # 标记失败
        await idempotency_service.mark_failed(
            event_id=callback.open_message_id,
            event_type="card_callback",
            error_message=str(e),
        )

        # 发送错误卡片
        await _send_error_card(callback, str(e))


async def _handle_confirm_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理确认执行动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    skill_name = action_value.get("skill", "")

    logger.info(
        "Handling confirm action",
        skill=skill_name,
        user_open_id=callback.open_id,
    )

    # TODO: 调用Skill执行服务
    # 从消息上下文获取原始请求参数，执行对应的Skill

    return {
        "success": True,
        "message": f"已开始执行 {skill_name}",
    }


async def _handle_cancel_action(
    callback: LarkCardCallback,
) -> Dict[str, Any]:
    """
    处理取消动作.

    Args:
        callback: 卡片回调

    Returns:
        Dict: 处理结果
    """
    logger.info(
        "Handling cancel action",
        user_open_id=callback.open_id,
    )

    return {
        "success": True,
        "message": "操作已取消",
    }


async def _handle_select_project_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理选择项目动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    project_id = action_value.get("project_id", "")

    logger.info(
        "Handling select project action",
        project_id=project_id,
        user_open_id=callback.open_id,
    )

    # TODO: 绑定用户与项目上下文

    return {
        "success": True,
        "message": f"已选择项目: {project_id}",
        "project_id": project_id,
    }


async def _handle_update_task_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理更新任务动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    task_id = action_value.get("task_id", "")
    progress = action_value.get("progress", 0)
    status = action_value.get("status", "")

    logger.info(
        "Handling update task action",
        task_id=task_id,
        progress=progress,
        status=status,
    )

    # TODO: 调用任务更新服务

    return {
        "success": True,
        "message": f"任务 {task_id} 已更新",
    }


async def _handle_acknowledge_risk_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理确认风险动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    risk_id = action_value.get("risk_id", "")

    logger.info(
        "Handling acknowledge risk action",
        risk_id=risk_id,
    )

    # TODO: 更新风险状态为已确认

    return {
        "success": True,
        "message": "风险已确认，将持续跟踪",
    }


async def _handle_approve_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理审批通过动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    approval_id = action_value.get("approval_id", "")

    logger.info(
        "Handling approve action",
        approval_id=approval_id,
    )

    # TODO: 更新审批状态

    return {
        "success": True,
        "message": "审批已通过",
    }


async def _handle_reject_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理审批拒绝动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    approval_id = action_value.get("approval_id", "")
    reason = action_value.get("reason", "")

    logger.info(
        "Handling reject action",
        approval_id=approval_id,
        reason=reason,
    )

    # TODO: 更新审批状态

    return {
        "success": True,
        "message": "审批已拒绝",
    }


async def _handle_retry_action(
    callback: LarkCardCallback,
    action_value: Dict[str, Any],
) -> Dict[str, Any]:
    """
    处理重试动作.

    Args:
        callback: 卡片回调
        action_value: 动作值

    Returns:
        Dict: 处理结果
    """
    original_action = action_value.get("original_action", "")

    logger.info(
        "Handling retry action",
        original_action=original_action,
    )

    # TODO: 重新执行原始操作

    return {
        "success": True,
        "message": "正在重新执行...",
    }


async def _send_success_card(
    callback: LarkCardCallback,
    result: Dict[str, Any],
) -> None:
    """
    发送成功结果卡片.

    Args:
        callback: 卡片回调
        result: 处理结果
    """
    lark_service = get_lark_service()

    await lark_service.send_success_card(
        receive_id=callback.open_chat_id,
        title="操作成功",
        message=result.get("message", "操作已完成"),
    )


async def _send_error_card(
    callback: LarkCardCallback,
    error_message: str,
) -> None:
    """
    发送错误结果卡片.

    Args:
        callback: 卡片回调
        error_message: 错误信息
    """
    lark_service = get_lark_service()

    await lark_service.send_error_card(
        receive_id=callback.open_chat_id,
        error_message=error_message,
    )


def _build_processing_response() -> Dict[str, Any]:
    """
    构建处理中响应卡片.

    Returns:
        Dict: 卡片内容
    """
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "type": "template",
            "data": {
                "template": {
                    "type": "card",
                    "header": {
                        "title": {"tag": "plain_text", "content": "正在处理"},
                        "template": "blue",
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": "⏳ 您的操作正在处理中，请稍候...",
                        },
                    ],
                },
            },
        },
    }


def _build_already_processed_response() -> Dict[str, Any]:
    """
    构建已处理响应卡片.

    Returns:
        Dict: 卡片内容
    """
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "type": "template",
            "data": {
                "template": {
                    "type": "card",
                    "header": {
                        "title": {"tag": "plain_text", "content": "已处理"},
                        "template": "grey",
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": "该操作已处理，请勿重复点击。",
                        },
                    ],
                },
            },
        },
    }