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
    if msg_type == "text":
        # Async processing for text messages
        background_tasks.add_task(
            _process_message_async,
            message_data=message,
            sender_id=sender_id,
            sender_user_id=sender_user_id,
            chat_type=chat_type,
        )
        return {"code": 0, "msg": "ok"}

    # v1.3.0新增：处理文件和图片消息
    if msg_type in ("file", "image", "media"):
        return await _handle_file_message(
            event_data=event_data,
            event_id=event_id,
            background_tasks=background_tasks,
        )

    # Other unhandled message types
    logger.debug("Unhandled message type", msg_type=msg_type)
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
    内部消息处理端点（供WebSocket调用）。

    无签名验证，直接处理消息。
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

        # ⚠️ 幂等检查：防止重复处理
        idempotency_service = get_message_idempotency_service()
        if not await idempotency_service.check_message(msg_id):
            logger.info("Message already processed, skipping", msg_id=msg_id)
            return {"code": 0, "msg": "ok", "result": {"skipped": True, "reason": "duplicate"}}

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


# ========== v1.3.0新增：文件消息处理 ==========


# 支持的文件消息类型
SUPPORTED_FILE_MSG_TYPES = ["file", "image", "media"]

# 文件大小限制（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024


async def _handle_file_message(
    event_data: Dict[str, Any],
    event_id: str,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Handle file/image message (v1.3.0新增).

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
    chat_id = message.get("chat_id", "")

    # Get sender ID
    sender_id = sender.get("sender_id", {}).get("open_id", "")

    # Parse file content
    content_str = message.get("content", "{}")
    try:
        content_obj = json.loads(content_str)
    except json.JSONDecodeError:
        logger.error("Failed to parse file message content", msg_id=msg_id)
        return {"code": -1, "msg": "Invalid file content"}

    # Extract file information
    file_key = content_obj.get("file_key", "")
    file_name = content_obj.get("name", "unknown_file")
    file_size = content_obj.get("size", 0)

    # File size check
    if file_size > MAX_FILE_SIZE:
        logger.warning("File size exceeds limit", file_size=file_size, max_size=MAX_FILE_SIZE)
        # Send error message
        try:
            lark_service = get_lark_service()
            await lark_service.send_text_message(
                receiver_id=chat_id,
                text=f"❌ 文件《{file_name}》大小超过限制（50MB），无法处理。",
            )
        except Exception:
            logger.exception("Failed to send file size error message")
        return {"code": 0, "msg": "File size exceeds limit"}

    # Idempotency check
    idempotency_service = get_message_idempotency_service()
    if not await idempotency_service.check_message(msg_id):
        logger.info("File message already processed", msg_id=msg_id)
        return {"code": 0, "msg": "ok"}

    logger.info(
        "File message received",
        msg_id=msg_id,
        msg_type=msg_type,
        file_name=file_name,
        file_key=file_key,
        sender_id=sender_id,
    )

    # Send processing notification
    try:
        lark_service = get_lark_service()
        await lark_service.send_text_message(
            receiver_id=chat_id,
            text=f"📄 正在处理文档《{file_name}》...",
        )
    except Exception:
        logger.exception("Failed to send processing notification")

    # Async processing
    background_tasks.add_task(
        _process_file_message_async,
        file_key=file_key,
        file_name=file_name,
        file_type=msg_type,
        file_size=file_size,
        sender_id=sender_id,
        chat_id=chat_id,
        chat_type=chat_type,
        message_id=msg_id,
        event_id=event_id,
    )

    # Return immediately
    return {"code": 0, "msg": "ok"}


async def _process_file_message_async(
    file_key: str,
    file_name: str,
    file_type: str,
    file_size: int,
    sender_id: str,
    chat_id: str,
    chat_type: str,
    message_id: str,
    event_id: str,
) -> None:
    """
    Async file message processing (v1.3.0新增).

    Args:
        file_key: Lark file key
        file_name: File name
        file_type: Message type (file/image/media)
        file_size: File size in bytes
        sender_id: Sender open_id
        chat_id: Chat ID
        chat_type: Chat type (p2p/group)
        message_id: Message ID
        event_id: Event ID
    """
    set_trace_id(message_id)
    idempotency_service = get_message_idempotency_service()

    try:
        logger.info(
            "Processing file message async",
            file_name=file_name,
            file_key=file_key,
            sender_id=sender_id,
        )

        # Get database session
        from app.core.database import get_async_session
        session = await anext(get_async_session())

        # Build user context
        user_context = {
            "user_id": sender_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
        }

        # Get group binding project if group chat
        if chat_type == "group":
            from app.services.context_service import ContextService
            context_service = ContextService(session)
            group_context = await context_service.get_group_context(chat_id)
            if group_context:
                user_context["group_binding_project_id"] = group_context.get("project_id")
                user_context["group_binding_project_name"] = group_context.get("project_name")

        # Call DocumentParseSkill
        from app.skills.document_parse_skill import DocumentParseSkill
        from app.orchestrator.schemas import SkillExecutionContext

        # Build skill context
        skill_context = SkillExecutionContext(
            user_id=sender_id,
            chat_id=chat_id,
            project_id=None,  # Will be inferred by classifier
            params={
                "file_key": file_key,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "message_id": message_id,
                "chat_type": chat_type,
            },
        )

        skill = DocumentParseSkill(
            context=skill_context,
            session=session,
        )

        result = await skill.execute()

        # Send result card
        lark_service = get_lark_service()
        if result.success:
            # Send success/pending card
            await lark_service.send_interactive_card(
                receiver_id=chat_id,
                card_data=result.presentation_data or {},
            )
        else:
            # Send error message
            await lark_service.send_text_message(
                receiver_id=chat_id,
                text=f"❌ 文档《{file_name}》处理失败：{result.error_message}",
            )

        # Mark completed
        await idempotency_service.mark_message_completed(message_id, None)

        logger.info(
            "File message processed successfully",
            file_name=file_name,
            success=result.success,
        )

    except Exception as e:
        logger.error(
            "Failed to process file message",
            file_name=file_name,
            error=str(e),
        )

        # Mark failed
        await idempotency_service.mark_failed(
            event_id=message_id,
            event_type="file_message",
            error_message=str(e),
        )

        # Send error message
        try:
            lark_service = get_lark_service()
            await lark_service.send_text_message(
                receiver_id=chat_id,
                text=f"❌ 文档《{file_name}》处理失败：{str(e)}",
            )
        except Exception:
            logger.exception("Failed to send file error message")

    finally:
        # Close session
        try:
            await session.close()
        except Exception:
            pass
