"""
PM Digital Employee - Message Dispatch Service
PM Digital Employee System - Message dispatch service

Handles Lark message dispatch and routing.
"""

import uuid
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.integrations.lark.schemas import LarkMessage
from app.orchestrator.orchestrator import get_orchestrator
from app.orchestrator.schemas import SkillExecutionResult
from app.integrations.lark.service import get_lark_service

logger = get_logger(__name__)


class MessageDispatchService:
    """
    Message dispatch service.

    Handles Lark message dispatch and routing.
    """

    def __init__(self) -> None:
        """Initialize message dispatch service."""
        self._orchestrator = get_orchestrator()
        self._lark_service = get_lark_service()

    async def dispatch(
        self,
        message: LarkMessage,
        sender_user_id: str,
    ) -> Dict[str, Any]:
        """
        Dispatch message.

        Args:
            message: Lark message
            sender_user_id: Sender user ID

        Returns:
            Dict: Processing result
        """
        trace_id = str(uuid.uuid4())

        logger.info(
            "Dispatching message",
            trace_id=trace_id,
            msg_id=message.message_id,
            sender_user_id=sender_user_id,
            chat_id=message.chat_id,
        )

        try:
            # Call orchestrator to process message
            result: SkillExecutionResult = await self._orchestrator.process_lark_message(
                message=message,
                sender_user_id=sender_user_id,
                trace_id=trace_id,
            )

            # Send response - use chat_id for P2P chat reply
            await self._send_response(
                chat_id=message.chat_id,
                user_id=sender_user_id,
                result=result,
            )

            return {
                "trace_id": trace_id,
                "success": result.success,
                "matched_skill": result.skill_name,
                "skill_name": result.skill_name,
                "response_message_id": None,  # TODO: get actual message ID
            }

        except Exception as e:
            logger.error(
                "Message dispatch failed",
                trace_id=trace_id,
                error=str(e),
            )

            # Send error notification
            await self._send_error_response(
                chat_id=message.chat_id,
                user_id=sender_user_id,
                error_message=str(e),
            )

            return {
                "trace_id": trace_id,
                "success": False,
                "error": str(e),
            }

    async def dispatch_lark(
        self,
        message: LarkMessage,
        sender_user_id: str,
    ) -> Dict[str, Any]:
        """
        Dispatch Lark message.

        Args:
            message: Lark message
            sender_user_id: Sender user ID

        Returns:
            Dict: Processing result
        """
        return await self.dispatch(message, sender_user_id)

    async def _send_response(
        self,
        chat_id: str,
        user_id: str,
        result: SkillExecutionResult,
    ) -> None:
        """
        Send response message.

        Args:
            chat_id: Chat ID (use for reply)
            user_id: User ID (fallback)
            result: Execution result
        """
        logger.info(
            "Sending response",
            user_id=user_id,
            chat_id=chat_id,
            success=result.success,
            presentation_type=result.presentation_type,
            has_presentation_data=bool(result.presentation_data),
        )

        # Determine target: prefer chat_id for P2P reply
        target_id = chat_id if chat_id else user_id
        use_chat_id = bool(chat_id)

        # 先检查是否失败，发送错误消息
        if not result.success and result.error_message:
            logger.info("Sending error card", user_id=user_id, chat_id=chat_id, error_message=result.error_message)
            try:
                if use_chat_id:
                    await self._lark_service.send_error_card_to_chat(
                        chat_id=target_id,
                        error_message=result.error_message,
                    )
                else:
                    await self._lark_service.send_error_card(
                        user_id=user_id,
                        error_message=result.error_message,
                    )
                logger.info("Error card sent successfully", user_id=user_id, chat_id=chat_id)
            except Exception as e:
                logger.error("Failed to send error card", user_id=user_id, chat_id=chat_id, error=str(e))
            return

        if result.requires_confirmation and result.confirmation_card:
            # Send confirmation card
            if use_chat_id:
                await self._lark_service.send_card_to_chat(
                    chat_id=target_id,
                    card=result.confirmation_card,
                )
            else:
                await self._lark_service.send_card(
                    user_id=user_id,
                    card=result.confirmation_card,
                )
        elif result.is_async:
            # Send async task accepted notification
            if use_chat_id:
                await self._lark_service.send_text_to_chat(
                    chat_id=target_id,
                    text=f"任务 {result.skill_name} 已接受，正在处理中...",
                )
            else:
                await self._lark_service.send_async_task_accepted(
                    user_id=user_id,
                    task_name=result.skill_name,
                )
        elif result.presentation_type == "text":
            # Send text message
            text = result.presentation_data.get("text", "") if result.presentation_data else ""
            logger.info("Sending text message", user_id=user_id, chat_id=chat_id, text_preview=text[:50])
            try:
                if use_chat_id:
                    await self._lark_service.send_text_to_chat(
                        chat_id=target_id,
                        text=text,
                    )
                else:
                    await self._lark_service.send_text(
                        user_id=user_id,
                        text=text,
                    )
                logger.info("Text message sent successfully", user_id=user_id, chat_id=chat_id)
            except Exception as e:
                logger.error("Failed to send text message", user_id=user_id, chat_id=chat_id, error=str(e))
        elif result.presentation_type == "markdown":
            # Send markdown message
            content = result.presentation_data.get("markdown", "") if result.presentation_data else ""
            if use_chat_id:
                await self._lark_service.send_text_to_chat(
                    chat_id=target_id,
                    text=content,
                )
            else:
                await self._lark_service.send_text(
                    user_id=user_id,
                    text=content,
                )
        elif result.presentation_type == "card":
            # Send card message
            card = result.presentation_data.get("card", {}) if result.presentation_data else {}
            if use_chat_id:
                await self._lark_service.send_card_to_chat(
                    chat_id=target_id,
                    card=card,
                )
            else:
                await self._lark_service.send_card(
                    user_id=user_id,
                    card=card,
                )
        elif not result.success:
            # Send error card
            if use_chat_id:
                await self._lark_service.send_error_card_to_chat(
                    chat_id=target_id,
                    error_message=result.error_message or "Processing failed.",
                )
            else:
                await self._lark_service.send_error_card(
                    user_id=user_id,
                    error_message=result.error_message or "Processing failed.",
                )

    async def _send_error_response(
        self,
        chat_id: str,
        user_id: str,
        error_message: str,
    ) -> None:
        """
        Send error response.

        Args:
            chat_id: Chat ID
            user_id: User ID
            error_message: Error message
        """
        target_id = chat_id if chat_id else user_id
        use_chat_id = bool(chat_id)
        
        try:
            if use_chat_id:
                await self._lark_service.send_error_card_to_chat(
                    chat_id=target_id,
                    error_message=f"Processing failed: {error_message}",
                )
            else:
                await self._lark_service.send_error_card(
                    user_id=user_id,
                    error_message=f"Processing failed: {error_message}",
                )
        except Exception as e:
            logger.error(
                "Failed to send error response",
                user_id=user_id,
                chat_id=chat_id,
                error=str(e),
            )


# Global service instance
_message_dispatch_service: Optional[MessageDispatchService] = None


def get_message_dispatch_service() -> MessageDispatchService:
    """Get message dispatch service instance."""
    global _message_dispatch_service
    if _message_dispatch_service is None:
        _message_dispatch_service = MessageDispatchService()
    return _message_dispatch_service
