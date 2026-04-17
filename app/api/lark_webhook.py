"""
PM Digital Employee - Lark Webhook
PM Digital Employee System - Lark event webhook receiver

Receives Lark event push messages (v2 format), verifies signature,
checks idempotency, and dispatches for async processing.
"""

import json
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Query, Request

from app.core.logging import get_logger, set_trace_id
from app.core.rate_limiter import limiter
from app.integrations.lark.schemas import LarkMessage
from app.integrations.lark.service import get_lark_service
from app.integrations.lark.signature import verify_lark_request, LarkSignatureVerifier
from app.services.idempotency_service import get_message_idempotency_service

logger = get_logger(__name__)

router = APIRouter(prefix="/lark/webhook", tags=["Lark Webhook"])

# 内部处理端点（用于WebSocket回调）
internal_router = APIRouter(prefix="/internal", tags=["Internal"])

# Context variable: current Lark event trace_id
_current_lark_event_id: ContextVar[Optional[str]] = ContextVar("current_lark_event_id", default=None)


def get_event_id() -> Optional[str]:
    """Get current event ID."""
    return _current_lark_event_id.get()


def set_event_id(event_id: str) -> None:
    """Set current event ID."""
    _current_lark_event_id.set(event_id)
    set_trace_id(event_id)


@router.get("")
async def health_check() -> Dict[str, str]:
    """
    Lark webhook health check.

    Returns:
        Dict: Health status
    """
    return {"status": "ok", "service": "lark-webhook"}


@router.post("")
@limiter.limit("100/minute")
async def receive_event(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Receive Lark event push (v2 format).

    Lark pushes events as POST JSON with schema:
    {"schema": "2.0", "header": {...}, "event": {...}}

    For URL verification, Lark POSTs: {"challenge": "xxx"}

    Args:
        request: FastAPI request object
        background_tasks: Background task runner

    Returns:
        Dict: Response result
    """
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        data = json.loads(body_str)

        # Handle URL verification challenge
        if "challenge" in data:
            logger.info("Lark URL challenge verification received")
            return LarkSignatureVerifier.handle_challenge(data["challenge"])

        # Verify signature from headers
        lark_signature = request.headers.get("X-Lark-Signature", "")
        lark_timestamp = request.headers.get("X-Lark-Request-Timestamp", "")
        lark_nonce = request.headers.get("X-Lark-Request-Nonce", "")

        try:
            verify_lark_request(
                signature=lark_signature,
                timestamp=lark_timestamp,
                nonce=lark_nonce,
                body=body_str,
            )
        except Exception as e:
            logger.warning("Lark signature verification failed", error=str(e))
            raise HTTPException(status_code=401, detail="Signature verification failed")

        # Parse v2 event format
        schema = data.get("schema", "")
        header = data.get("header", {})
        event = data.get("event", {})

        event_id = header.get("event_id", "")
        event_type = header.get("type", "")

        # Set trace_id
        set_event_id(event_id)

        logger.info(
            "Lark event received",
            event_id=event_id,
            event_type=event_type,
            schema=schema,
        )

        # Handle message events
        if event_type == "im.message.receive_v1":
            return await _handle_message_receive(
                event_data=event,
                event_id=event_id,
                background_tasks=background_tasks,
            )

        # Other event types
        logger.debug("Unhandled event type", event_type=event_type)
        return {"code": 0, "msg": "ok"}

    except json.JSONDecodeError:
        logger.error("Failed to parse webhook request body")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to handle webhook request", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error")


async def _handle_message_receive(
    event_data: Dict[str, Any],
    event_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Handle im.message.receive_v1 event.

    Args:
        event_data: Event payload
        event_id: Event ID
        background_tasks: Background task runner

    Returns:
        Dict: Response result
    """
    message = event_data.get("message", {})
    sender = event_data.get("sender", {})

    msg_id = message.get("message_id", "")
    msg_type = message.get("message_type", "")
    chat_type = message.get("chat_type", "p2p")

    # Get sender ID (prefer open_id)
    sender_id = sender.get("sender_id", {}).get("open_id", "")
    sender_user_id = sender.get("sender_id", {}).get("user_id", "")

    logger.info(
        "Lark message received",
        msg_id=msg_id,
        msg_type=msg_type,
        chat_type=chat_type,
        sender_open_id=sender_id,
    )

    # Idempotency check
    idempotency_service = get_message_idempotency_service()
    if not await idempotency_service.check_message(msg_id):
        logger.info("Message already processed", msg_id=msg_id)
        return {"code": 0, "msg": "ok"}

    # Only handle text messages for now
    if msg_type != "text":
        logger.debug("Unhandled message type", msg_type=msg_type)
        return {"code": 0, "msg": "ok"}

    # Async processing
    background_tasks.add_task(
        _process_message_async,
        message_data=message,
        sender_id=sender_id,
        sender_user_id=sender_user_id,
        chat_type=chat_type,
    )

    # Return immediately (Lark expects response within 3 seconds)
    return {"code": 0, "msg": "ok"}


async def _process_message_async(
    message_data: Dict[str, Any],
    sender_id: str,
    sender_user_id: str,
    chat_type: str,
) -> None:
    """
    Async message processing.

    Args:
        message_data: Message data
        sender_id: Sender open_id
        sender_user_id: Sender user_id
        chat_type: Chat type (p2p/group)
    """
    msg_id = message_data.get("message_id", "")
    set_event_id(msg_id)

    idempotency_service = get_message_idempotency_service()

    try:
        logger.info(
            "Processing message async",
            msg_id=msg_id,
            sender_id=sender_id,
        )

        # Extract text content
        content = ""
        msg_content = message_data.get("content", "{}")
        try:
            content_obj = json.loads(msg_content)
            content = content_obj.get("text", "")
        except json.JSONDecodeError:
            content = msg_content

        # Build Lark message object
        message = LarkMessage(
            message_id=msg_id,
            chat_id=message_data.get("chat_id", ""),
            chat_type=chat_type,
            message_type="text",
            content=content,
            sender_user_id=sender_user_id,
            sender_open_id=sender_id,
            create_time=message_data.get("create_time", ""),
            parent_id=message_data.get("parent_id", ""),
            root_id=message_data.get("root_id", ""),
        )

        # Import message dispatch service (lazy import to avoid circular deps)
        from app.services.message_dispatch_service import get_message_dispatch_service

        dispatch_service = get_message_dispatch_service()

        # Dispatch for processing
        result = await dispatch_service.dispatch_lark(
            message=message,
            sender_user_id=sender_id,
        )

        # Mark completed
        await idempotency_service.mark_message_completed(
            msg_id,
            result.get("response_message_id"),
        )

        logger.info("Message processed successfully", msg_id=msg_id)

    except Exception as e:
        logger.error(
            "Failed to process message",
            msg_id=msg_id,
            error=str(e),
        )

        # Mark failed
        await idempotency_service.mark_failed(
            event_id=msg_id,
            event_type="message",
            error_message=str(e),
        )

        # Send error card
        try:
            lark_service = get_lark_service()
            await lark_service.send_error_card(
                user_id=sender_id,
                error_message="Message processing failed, please try again later.",
            )
        except Exception:
            logger.exception("Failed to send error card")


# ========== 内部处理端点（用于WebSocket回调） ==========


@internal_router.post("/process-message")
async def internal_process_message(request: Request) -> Dict[str, Any]:
    """
    内部消息处理端点（供WebSocket调用）。    无签名验证，直接处理消息。
    """
    try:
        data = await request.json()

        message_data = data.get("message", {})
        sender_id = data.get("sender_id", "")
        sender_user_id = data.get("sender_user_id") or sender_id  # Use sender_id as fallback
        chat_type = data.get("chat_type", "p2p")
        msg_id = message_data.get("message_id", "")
        set_trace_id(msg_id)

        logger.info("Internal process message", msg_id=msg_id, sender_id=sender_id, sender_user_id=sender_user_id)

        # 构建 LarkMessage
        message = LarkMessage(
            message_id=msg_id,
            chat_id=message_data.get("chat_id", ""),
            chat_type=chat_type,
            message_type=message_data.get("message_type", "text"),
            content=message_data.get("content", ""),
            sender_user_id=sender_user_id,
            sender_open_id=sender_id,
            create_time=message_data.get("create_time", ""),
            parent_id=message_data.get("parent_id", ""),
            root_id=message_data.get("root_id", ""),
        )

        # 调用消息处理服务
        from app.services.message_dispatch_service import get_message_dispatch_service
        dispatch_service = get_message_dispatch_service()
        result = await dispatch_service.dispatch_lark(
            message=message,
            sender_user_id=sender_id,
        )

        logger.info("Internal process done", msg_id=msg_id, success=result.get("success"))
        return {"code": 0, "msg": "ok", "result": result}

    except Exception as e:
        logger.error("Internal process failed", error=str(e))
        return {"code": -1, "msg": str(e)}
