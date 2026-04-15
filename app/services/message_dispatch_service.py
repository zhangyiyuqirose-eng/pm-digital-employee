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
        )

        try:
            # Call orchestrator to process message
            result: SkillExecutionResult = await self._orchestrator.process_lark_message(
                message=message,
                sender_user_id=sender_user_id,
                trace_id=trace_id,
            )

            # Send response
            await self._send_response(
                user_id=sender_user_id,
                result=result,
            )

            return {
                "trace_id": trace_id,
                "success": result.success,
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
        user_id: str,
        result: SkillExecutionResult,
    ) -> None:
        """
        Send response message.

        Args:
            user_id: User ID
            result: Execution result
        """
        if result.requires_confirmation and result.confirmation_card:
            # Send confirmation card
            await self._lark_service.send_card(
                user_id=user_id,
                card=result.confirmation_card,
            )
        elif result.is_async:
            # Send async task accepted notification
            await self._lark_service.send_async_task_accepted(
                user_id=user_id,
                task_name=result.skill_name,
            )
        elif result.presentation_type == "text":
            # Send text message
            text = result.presentation_data.get("text", "") if result.presentation_data else ""
            await self._lark_service.send_text(
                user_id=user_id,
                text=text,
            )
        elif result.presentation_type == "markdown":
            # Send markdown message
            content = result.presentation_data.get("markdown", "") if result.presentation_data else ""
            await self._lark_service.send_text(
                user_id=user_id,
                text=content,
            )
        elif result.presentation_type == "card":
            # Send card message
            card = result.presentation_data.get("card", {}) if result.presentation_data else {}
            await self._lark_service.send_card(
                user_id=user_id,
                card=card,
            )
        elif not result.success:
            # Send error card
            await self._lark_service.send_error_card(
                user_id=user_id,
                error_message=result.error_message or "Processing failed.",
            )

    async def _send_error_response(
        self,
        user_id: str,
        error_message: str,
    ) -> None:
        """
        Send error response.

        Args:
            user_id: User ID
            error_message: Error message
        """
        try:
            await self._lark_service.send_error_card(
                user_id=user_id,
                error_message=f"Processing failed: {error_message}",
            )
        except Exception as e:
            logger.error(
                "Failed to send error response",
                user_id=user_id,
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
