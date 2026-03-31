"""
PM Digital Employee - Lark Webhook
项目经理数字员工系统 - 飞书事件Webhook接收接口

接收飞书消息、事件推送，验签、幂等、异步分发处理。
"""

import json
from contextvars import ContextVar
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request

from app.core.config import settings
from app.core.exceptions import ErrorCode, LarkError
from app.core.logging import get_logger, set_trace_id
from app.integrations.lark.schemas import (
    LarkCardCallback,
    LarkEvent,
    LarkEventHeader,
    LarkMessage,
    LarkMessageEvent,
    LarkWebhookRequest,
)
from app.integrations.lark.service import get_lark_service
from app.integrations.lark.signature import verify_lark_request, LarkSignatureVerifier
from app.services.idempotency_service import (
    get_message_idempotency_service,
    get_card_callback_idempotency_service,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/lark/webhook", tags=["Lark Webhook"])

# 上下文变量：当前飞书事件trace_id
_current_lark_event_id: ContextVar[Optional[str]] = ContextVar("current_lark_event_id", default=None)


def get_event_id() -> Optional[str]:
    """获取当前事件ID."""
    return _current_lark_event_id.get()


def set_event_id(event_id: str) -> None:
    """设置当前事件ID."""
    _current_lark_event_id.set(event_id)
    set_trace_id(event_id)


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

    Raises:
        HTTPException: 验证失败
    """
    if not settings.lark.verify_signature:
        return True

    # 获取请求体
    body = await request.body()
    body_str = body.decode("utf-8")

    # 验证签名
    try:
        verify_lark_request(
            timestamp=x_lark_request_timestamp or "",
            nonce=x_lark_request_nonce or "",
            body=body_str,
            signature=x_lark_signature or "",
        )
        return True
    except LarkError as e:
        logger.warning(
            "Lark signature verification failed",
            error=str(e),
        )
        raise HTTPException(
            status_code=401,
            detail="Signature verification failed",
        )


@router.post("/message")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_request_signature),
) -> Dict[str, Any]:
    """
    接收飞书消息事件.

    飞书收到用户消息后推送到此接口。
    验签、幂等检查后，异步分发处理。

    Args:
        request: FastAPI请求对象
        background_tasks: 后台任务

    Returns:
        Dict: 响应结果
    """
    # 获取请求体
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        # 解析请求
        webhook_request = LarkWebhookRequest.model_validate_json(body_str)

        # 处理URL验证
        if webhook_request.type == "url_verification":
            logger.info("Lark URL verification request received")
            return {
                "challenge": LarkSignatureVerifier.verify_url(
                    webhook_request.challenge or "",
                ),
            }

        # 解析事件
        if webhook_request.header and webhook_request.event:
            event = LarkEvent(
                schema_version=webhook_request.schema,
                header=LarkEventHeader.model_validate(webhook_request.header),
                event=webhook_request.event,
            )
        else:
            logger.warning("Invalid webhook request format")
            raise HTTPException(status_code=400, detail="Invalid request format")

        # 获取事件ID用于trace
        event_id = event.header.event_id
        set_event_id(event_id)

        # 检查事件类型
        event_type = event.header.event_type
        logger.info(
            "Lark event received",
            event_id=event_id,
            event_type=event_type,
        )

        # 消息事件处理
        if event_type.startswith("im.message"):
            return await _handle_message_event(
                event=event,
                background_tasks=background_tasks,
            )

        # 其他事件类型
        logger.debug(
            "Unhandled event type",
            event_type=event_type,
        )
        return {"code": 0, "msg": "success"}

    except json.JSONDecodeError:
        logger.error("Failed to parse webhook request body")
        raise HTTPException(status_code=400, detail="Invalid JSON")


@router.post("/event")
async def receive_event(
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_request_signature),
) -> Dict[str, Any]:
    """
    接收飞书其他事件.

    处理群成员变更、审批事件等。

    Args:
        request: FastAPI请求对象
        background_tasks: 后台任务

    Returns:
        Dict: 响应结果
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        webhook_request = LarkWebhookRequest.model_validate_json(body_str)

        # URL验证
        if webhook_request.type == "url_verification":
            return {"challenge": LarkSignatureVerifier.verify_url(webhook_request.challenge or "")}

        if webhook_request.header and webhook_request.event:
            event = LarkEvent(
                schema_version=webhook_request.schema,
                header=LarkEventHeader.model_validate(webhook_request.header),
                event=webhook_request.event,
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid request format")

        event_id = event.header.event_id
        set_event_id(event_id)

        event_type = event.header.event_type
        logger.info(
            "Lark event received",
            event_id=event_id,
            event_type=event_type,
        )

        # 异步处理事件
        background_tasks.add_task(
            _process_event_async,
            event,
        )

        return {"code": 0, "msg": "success"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")


@router.post("/url_verification")
async def url_verification(
    request: Request,
) -> Dict[str, Any]:
    """
    飞书URL验证接口.

    飞书配置事件订阅时需要验证URL可达性。

    Args:
        request: FastAPI请求对象

    Returns:
        Dict: challenge响应
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        data = json.loads(body_str)
        challenge = data.get("challenge", "")

        logger.info("Lark URL verification successful")

        return {"challenge": challenge}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")


async def _handle_message_event(
    event: LarkEvent,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    处理消息事件.

    Args:
        event: 飞书事件
        background_tasks: 后台任务

    Returns:
        Dict: 响应结果
    """
    event_body = event.event

    # 构建消息事件对象
    try:
        message_event = LarkMessageEvent.model_validate(event_body)
        message = message_event.message
    except Exception as e:
        logger.error(
            "Failed to parse message event",
            error=str(e),
        )
        return {"code": 0, "msg": "parse error"}

    # 幂等检查
    idempotency_service = get_message_idempotency_service()
    if not await idempotency_service.check_message(message.message_id):
        logger.info(
            "Message already processed",
            message_id=message.message_id,
        )
        return {"code": 0, "msg": "duplicate"}

    # 检查消息类型
    if message.message_type not in ("text", "post", "interactive"):
        logger.debug(
            "Unsupported message type",
            message_type=message.message_type,
        )
        # 标记完成
        await idempotency_service.mark_message_completed(message.message_id)
        return {"code": 0, "msg": "unsupported type"}

    # 获取发送者信息
    sender = message_event.sender
    sender_id = sender.get("sender_id", {})
    open_id = sender_id.get("open_id", "")

    if not open_id:
        logger.warning("No sender open_id in message")
        return {"code": 0, "msg": "no sender"}

    # 过滤机器人自己发送的消息
    if sender.get("sender_type") == "app":
        logger.debug("Ignoring app self-sent message")
        return {"code": 0, "msg": "self-sent"}

    # 异步处理消息
    background_tasks.add_task(
        _process_message_async,
        message,
        open_id,
        event.header.event_id,
    )

    # 立即返回，飞书要求1秒内响应
    return {"code": 0, "msg": "accepted"}


async def _process_message_async(
    message: LarkMessage,
    sender_open_id: str,
    event_id: str,
) -> None:
    """
    异步处理消息.

    Args:
        message: 消息对象
        sender_open_id: 发送者OpenID
        event_id: 事件ID
    """
    set_event_id(event_id)

    idempotency_service = get_message_idempotency_service()

    try:
        logger.info(
            "Processing message async",
            message_id=message.message_id,
            chat_id=message.chat_id,
            sender_open_id=sender_open_id,
        )

        # 导入消息分发服务（延迟导入避免循环依赖）
        from app.services.message_dispatch_service import get_message_dispatch_service

        dispatch_service = get_message_dispatch_service()

        # 分发处理消息
        result = await dispatch_service.dispatch(
            message=message,
            sender_open_id=sender_open_id,
        )

        # 标记处理完成
        await idempotency_service.mark_message_completed(
            message.message_id,
            result.get("response_message_id"),
        )

        logger.info(
            "Message processed successfully",
            message_id=message.message_id,
        )

    except Exception as e:
        logger.error(
            "Failed to process message",
            message_id=message.message_id,
            error=str(e),
        )

        # 标记处理失败
        await idempotency_service.mark_failed(
            event_id=message.message_id,
            event_type="message",
            error_message=str(e),
        )

        # 发送错误提示
        try:
            lark_service = get_lark_service()
            await lark_service.send_error_card(
                receive_id=message.chat_id,
                error_message="消息处理失败，请稍后重试",
            )
        except Exception:
            logger.exception("Failed to send error card")


async def _process_event_async(
    event: LarkEvent,
) -> None:
    """
    异步处理飞书事件.

    Args:
        event: 飞书事件
    """
    set_event_id(event.header.event_id)

    try:
        event_type = event.header.event_type
        event_body = event.event

        logger.info(
            "Processing event async",
            event_id=event.header.event_id,
            event_type=event_type,
        )

        # 根据事件类型分发
        if event_type.startswith("im.chat.member"):
            await _handle_chat_member_event(event_type, event_body)
        elif event_type.startswith("approval"):
            await _handle_approval_event(event_type, event_body)
        else:
            logger.debug(
                "Unhandled event type in async processing",
                event_type=event_type,
            )

    except Exception as e:
        logger.error(
            "Failed to process event",
            event_id=event.header.event_id,
            error=str(e),
        )


async def _handle_chat_member_event(
    event_type: str,
    event_body: Dict[str, Any],
) -> None:
    """
    处理群成员变更事件.

    Args:
        event_type: 事件类型
        event_body: 事件内容
    """
    logger.info(
        "Handling chat member event",
        event_type=event_type,
    )

    # 获取群ID
    chat_id = event_body.get("chat_id", "")

    # TODO: 同步群成员信息到数据库
    # 这里可以触发群成员缓存更新


async def _handle_approval_event(
    event_type: str,
    event_body: Dict[str, Any],
) -> None:
    """
    处理审批事件.

    Args:
        event_type: 事件类型
        event_body: 事件内容
    """
    logger.info(
        "Handling approval event",
        event_type=event_type,
    )

    # TODO: 处理审批状态变更
    # 根据审批Code查询对应的审批记录并更新状态