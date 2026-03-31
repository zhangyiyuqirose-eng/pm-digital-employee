"""
PM Digital Employee - Message Dispatch Service
项目经理数字员工系统 - 消息分发服务

处理飞书消息的分发和路由。
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
    消息分发服务.

    处理飞书消息的分发和路由。
    """

    def __init__(self) -> None:
        """初始化消息分发服务."""
        self._orchestrator = get_orchestrator()
        self._lark_service = get_lark_service()

    async def dispatch(
        self,
        message: LarkMessage,
        sender_open_id: str,
    ) -> Dict[str, Any]:
        """
        分发消息.

        Args:
            message: 飞书消息
            sender_open_id: 发送者OpenID

        Returns:
            Dict: 处理结果
        """
        trace_id = str(uuid.uuid4())

        logger.info(
            "Dispatching message",
            trace_id=trace_id,
            message_id=message.message_id,
            chat_id=message.chat_id,
            sender_open_id=sender_open_id,
        )

        try:
            # 调用编排器处理消息
            result: SkillExecutionResult = await self._orchestrator.process_message(
                message=message,
                sender_open_id=sender_open_id,
                trace_id=trace_id,
            )

            # 发送响应
            await self._send_response(
                chat_id=message.chat_id,
                result=result,
            )

            return {
                "trace_id": trace_id,
                "success": result.success,
                "response_message_id": None,  # TODO: 获取实际消息ID
            }

        except Exception as e:
            logger.error(
                "Message dispatch failed",
                trace_id=trace_id,
                error=str(e),
            )

            # 发送错误提示
            await self._send_error_response(
                chat_id=message.chat_id,
                error_message=str(e),
            )

            return {
                "trace_id": trace_id,
                "success": False,
                "error": str(e),
            }

    async def _send_response(
        self,
        chat_id: str,
        result: SkillExecutionResult,
    ) -> None:
        """
        发送响应消息.

        Args:
            chat_id: 会话ID
            result: 执行结果
        """
        if result.requires_confirmation and result.confirmation_card:
            # 发送确认卡片
            await self._lark_service.send_card(
                receive_id=chat_id,
                card=result.confirmation_card,
            )
        elif result.is_async:
            # 发送异步任务受理提示
            await self._lark_service.send_async_task_accepted(
                receive_id=chat_id,
                task_name=result.skill_name,
            )
        elif result.presentation_type == "text":
            # 发送文本消息
            text = result.presentation_data.get("text", "") if result.presentation_data else ""
            await self._lark_service.send_text(
                receive_id=chat_id,
                text=text,
            )
        elif result.presentation_type == "card":
            # 发送卡片消息
            card = result.presentation_data.get("card", {}) if result.presentation_data else {}
            await self._lark_service.send_card(
                receive_id=chat_id,
                card=card,
            )
        elif not result.success:
            # 发送错误消息
            await self._lark_service.send_error_card(
                receive_id=chat_id,
                error_message=result.error_message or "处理失败",
            )

    async def _send_error_response(
        self,
        chat_id: str,
        error_message: str,
    ) -> None:
        """
        发送错误响应.

        Args:
            chat_id: 会话ID
            error_message: 错误信息
        """
        try:
            await self._lark_service.send_error_card(
                receive_id=chat_id,
                error_message=f"处理失败: {error_message}",
            )
        except Exception as e:
            logger.error(
                "Failed to send error response",
                chat_id=chat_id,
                error=str(e),
            )


# 全局服务实例
_message_dispatch_service: Optional[MessageDispatchService] = None


def get_message_dispatch_service() -> MessageDispatchService:
    """获取消息分发服务实例."""
    global _message_dispatch_service
    if _message_dispatch_service is None:
        _message_dispatch_service = MessageDispatchService()
    return _message_dispatch_service