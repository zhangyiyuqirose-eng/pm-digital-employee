"""
PM Digital Employee - Lark WebSocket Client
PM Digital Employee System - Lark WebSocket long connection

Receives Lark events via WebSocket (no need for public HTTPS endpoint).
"""

import asyncio
import json
import threading
import multiprocessing
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger, set_trace_id
from app.integrations.lark.schemas import LarkMessage
from app.services.idempotency_service import get_message_idempotency_service

logger = get_logger(__name__)

# Global websocket process
_ws_process: Optional[multiprocessing.Process] = None


def handle_p2p_chat_entered(data: Any) -> None:
    """
    Handle bot entering P2P chat event.
    """
    try:
        logger.info("Bot entered P2P chat via WebSocket", data=str(data)[:100])
    except Exception as e:
        logger.error("Failed to handle P2P chat entered event", error=str(e))


def handle_message_read_v1(data: Any) -> None:
    """
    Handle im.message.message_read_v1 event (message read by user).
    Just acknowledge, no action needed.
    """
    try:
        # Extract reader info for logging
        if hasattr(data, 'event'):
            event = data.event
            reader = getattr(event, 'reader', None)
            msg_id = getattr(event, 'message_id', '')
            if reader and hasattr(reader, 'read_time'):
                logger.debug("Message read", msg_id=msg_id, read_time=reader.read_time)
    except Exception as e:
        logger.error("Failed to handle message read event", error=str(e))


def handle_im_message_receive_v1(data: Any) -> None:
    """
    Handle im.message.receive_v1 event from WebSocket.
    """
    try:
        # Log the raw data structure for debugging
        logger.info("WebSocket raw message data", raw=str(data)[:500])

        # SDK passes a P2ImMessageReceiveV1 object, extract fields directly
        # Try to get the event object's attributes directly
        if hasattr(data, 'event'):
            event_obj = data.event
        else:
            event_obj = data

        # Try direct attribute access first (SDK objects have these attributes)
        if hasattr(event_obj, 'message'):
            message = event_obj.message
            sender = event_obj.sender if hasattr(event_obj, 'sender') else None

            # Extract message attributes
            msg_id = getattr(message, 'message_id', '') if message else ''
            msg_type = getattr(message, 'message_type', '') if message else ''
            chat_type = getattr(message, 'chat_type', 'p2p') if message else 'p2p'
            chat_id = getattr(message, 'chat_id', '') if message else ''
            msg_content = getattr(message, 'content', '{}') if message else '{}'

            # Extract sender attributes
            if sender and hasattr(sender, 'sender_id'):
                sender_id_obj = sender.sender_id
                sender_id = getattr(sender_id_obj, 'open_id', '') if sender_id_obj else ''
                sender_user_id = getattr(sender_id_obj, 'user_id', '') if sender_id_obj else ''
            else:
                sender_id = ''
                sender_user_id = ''
        else:
            # Fallback: try JSON parsing
            event_dict = json.loads(json.dumps(data, default=lambda o: o.__dict__))

            message = event_dict.get("message", {})
            sender = event_dict.get("sender", {})

            msg_id = message.get("message_id", "")
            msg_type = message.get("message_type", "")
            chat_type = message.get("chat_type", "p2p")
            chat_id = message.get("chat_id", "")
            msg_content = message.get("content", "{}")

            sender_id = sender.get("sender_id", {}).get("open_id", "") if sender else ''
            sender_user_id = sender.get("sender_id", {}).get("user_id", "") if sender else ''

        set_trace_id(msg_id)

        logger.info(
            "WebSocket message received",
            msg_id=msg_id,
            msg_type=msg_type,
            chat_type=chat_type,
            sender_open_id=sender_id,
            sender_user_id=sender_user_id,
        )

        if msg_type != "text":
            logger.debug("Unhandled message type via WebSocket", msg_type=msg_type)
            return

        content = ""
        try:
            content_obj = json.loads(msg_content)
            content = content_obj.get("text", "")
        except json.JSONDecodeError:
            content = msg_content

        # Ensure sender_user_id is not None (use sender_id as fallback)
        if not sender_user_id:
            sender_user_id = sender_id

        # For now, just log and call internal processing endpoint
        _process_message_internal(
            message={
                "message_id": msg_id,
                "chat_id": chat_id,
                "chat_type": chat_type,
                "message_type": msg_type,
                "content": msg_content,
                "create_time": "",
            },
            sender_id=sender_id,
            sender_user_id=sender_user_id or sender_id,
        )

    except Exception as e:
        logger.error("Failed to handle WebSocket message", error=str(e), exc_info=True)


def _process_message_internal(message: Dict[str, Any], sender_id: str, sender_user_id: str) -> None:
    """
    Call internal processing endpoint via HTTP.
    This allows WebSocket (sync) to call async message processing.
    """
    try:
        import httpx

        # Call internal endpoint
        internal_url = f"http://127.0.0.1:8000/internal/process-message"
        resp = httpx.post(
            internal_url,
            json={
                "message": message,
                "sender_id": sender_id,
                "sender_user_id": sender_user_id,
                "chat_type": message.get("chat_type", "p2p"),
            },
            timeout=30.0,
        )

        result = resp.json()
        if result.get("code") == 0:
            logger.info("Internal processing success", msg_id=message.get("message_id"))
        else:
            logger.error("Internal processing failed", error=result.get("msg"))

    except Exception as e:
        logger.error("Failed to call internal endpoint", error=str(e))


def _run_ws_process(app_id: str, app_secret: str, api_domain: str) -> None:
    """
    Run WebSocket client in a separate process (clean event loop).
    """
    # Import SDK inside the process to avoid event loop conflicts
    from lark_oapi.ws import Client
    from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder
    from lark_oapi.core.enum import LogLevel

    print(f"[Lark WS Process] Starting with app_id={app_id[:8]}...")

    # Create event dispatcher
    event_handler = EventDispatcherHandlerBuilder(
        encrypt_key="",
        verification_token="",
    ).register_p2_im_message_receive_v1(handle_im_message_receive_v1).register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(handle_p2p_chat_entered).register_p2_im_message_message_read_v1(handle_message_read_v1).build()

    # Create WebSocket client
    client = Client(
        app_id=app_id,
        app_secret=app_secret,
        log_level=LogLevel.INFO,
        event_handler=event_handler,
        domain=api_domain,
        auto_reconnect=True,
    )

    print("[Lark WS Process] Client created, starting connection...")

    # Start the blocking WebSocket loop
    try:
        client.start()
        print("[Lark WS Process] WebSocket loop ended")
    except Exception as e:
        print(f"[Lark WS Process] Error: {e}")


def start_lark_websocket() -> None:
    """
    Start Lark WebSocket long connection in a separate thread.
    """
    global _ws_process

    if not settings.lark_configured:
        logger.warning("Lark not configured, skipping WebSocket connection")
        return

    if _ws_process is not None:
        logger.info("Lark WebSocket already running")
        return

    logger.info(
        "Starting Lark WebSocket thread",
        app_id=settings.lark_app_id[:8] + "...",
    )

    # Start in a separate thread with its own event loop
    def _run_ws_thread():
        try:
            # Import SDK inside the thread
            from lark_oapi.ws import Client
            from lark_oapi.event.dispatcher_handler import EventDispatcherHandlerBuilder
            from lark_oapi.core.enum import LogLevel

            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            logger.info("[Lark WS Thread] Creating client...")

            # Create event dispatcher
            event_handler = EventDispatcherHandlerBuilder(
                encrypt_key="",
                verification_token="",
            ).register_p2_im_message_receive_v1(handle_im_message_receive_v1).register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(handle_p2p_chat_entered).register_p2_im_message_message_read_v1(handle_message_read_v1).build()

            # Create WebSocket client
            client = Client(
                app_id=settings.lark_app_id,
                app_secret=settings.lark_app_secret,
                log_level=LogLevel.INFO,
                event_handler=event_handler,
                domain=settings.lark_api_domain,
                auto_reconnect=True,
            )

            logger.info("[Lark WS Thread] Client created, starting connection...")

            # Run the blocking WebSocket loop (SDK's start is synchronous)
            client.start()

            logger.info("[Lark WS Thread] WebSocket loop ended")

        except Exception as e:
            logger.error("[Lark WS Thread] Error", error=str(e))

    import threading
    _ws_process = threading.Thread(target=_run_ws_thread, daemon=True)
    _ws_process.start()

    logger.info("Lark WebSocket thread launched")


def stop_lark_websocket() -> None:
    """
    Stop Lark WebSocket connection.
    """
    global _ws_process

    if _ws_process is not None:
        logger.info("Stopping Lark WebSocket thread")
        # Thread is daemon, will exit when main process exits
        _ws_process = None
        logger.info("Lark WebSocket thread stopped")