"""
PM Digital Employee - Lark Service
PM Digital Employee System - Lark business service layer

Encapsulates common Lark operations: message sending, card building,
user info retrieval, etc.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.lark.client import LarkClient, LarkError, get_lark_client
from app.integrations.lark.schemas import LarkCardBuilder

logger = get_logger(__name__)


class LarkService:
    """
    Lark business service.

    Wraps Lark client with higher-level business operations.
    """

    def __init__(self, client: Optional[LarkClient] = None) -> None:
        """
        Initialize Lark service.

        Args:
            client: Lark client instance
        """
        self._client = client or get_lark_client()

    @property
    def client(self) -> LarkClient:
        """Get Lark client."""
        return self._client

    # ==================== Message sending ====================

    async def send_text(
        self,
        user_id: str,
        text: str,
    ) -> Dict:
        """
        Send text message to user.

        Args:
            user_id: Receiver user ID (open_id)
            text: Text content

        Returns:
            Dict: Send result
        """
        return await self._client.send_text_message(
            receive_id=user_id,
            text=text,
        )

    async def send_text_to_chat(
        self,
        chat_id: str,
        text: str,
    ) -> Dict:
        """
        Send text message to group chat.

        Args:
            chat_id: Group chat ID
            text: Text content

        Returns:
            Dict: Send result
        """
        return await self._client.send_text_to_chat(
            chat_id=chat_id,
            text=text,
        )

    async def send_card(
        self,
        user_id: str,
        card: Dict[str, Any],
    ) -> Dict:
        """
        Send interactive card message to user.

        Args:
            user_id: Receiver user ID (open_id)
            card: Card JSON (LarkCardBuilder output)

        Returns:
            Dict: Send result
        """
        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    async def send_card_to_chat(
        self,
        chat_id: str,
        card: Dict[str, Any],
    ) -> Dict:
        """
        Send interactive card message to group chat.

        Args:
            chat_id: Group chat ID
            card: Card JSON

        Returns:
            Dict: Send result
        """
        # 飞书Interactive卡片需要直接发送card内容，不需要wrapper
        # 正确格式: {"type": "interactive", "config":..., "header":..., "elements":...}
        # 或者直接把card作为content（SDK会处理）
        return await self._client.send_to_chat(
            chat_id=chat_id,
            msg_type="interactive",
            content=card,
        )

    # ==================== User info ====================

    async def get_user_info(self, user_id: str) -> Dict:
        """
        Get user info.

        Args:
            user_id: User ID

        Returns:
            Dict: User info
        """
        return await self._client.get_user_info(user_id)

    async def get_user_name(self, user_id: str) -> str:
        """
        Get user display name.

        Args:
            user_id: User ID

        Returns:
            str: User display name
        """
        try:
            user = await self.get_user_info(user_id)
            return user.get("data", {}).get("user", {}).get("name", user_id)
        except LarkError:
            return user_id

    # ==================== Chat info ====================

    async def get_chat_info(self, chat_id: str) -> Dict:
        """
        Get group chat info.

        Args:
            chat_id: Group chat ID

        Returns:
            Dict: Chat info
        """
        return await self._client.get_chat_info(chat_id)

    # ==================== Card building ====================

    def create_card(self) -> LarkCardBuilder:
        """
        Create card builder.

        Returns:
            LarkCardBuilder: Card builder instance
        """
        return LarkCardBuilder()

    async def send_clarification_card(
        self,
        user_id: str,
        matched_skill: str,
        skill_description: str,
        confidence: float,
    ) -> Dict:
        """
        Send intent clarification card.

        Args:
            user_id: Receiver user ID
            matched_skill: Matched skill name
            skill_description: Skill description
            confidence: Confidence score

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_button_interaction(
            title="Please confirm your intent",
            desc=f"Detected you may want: **{matched_skill}**\n{skill_description}\nConfidence: {confidence:.0%}",
            buttons=[
                {"text": "Confirm", "key": f"confirm:{matched_skill}"},
                {"text": "Cancel", "key": "cancel"},
            ],
        )

        return await self.send_card(user_id, card)

    async def send_clarification_card_to_chat(
        self,
        chat_id: str,
        matched_skill: str,
        skill_description: str,
        confidence: float,
    ) -> Dict:
        """
        Send intent clarification card to group chat.

        Args:
            chat_id: Group chat ID
            matched_skill: Matched skill name
            skill_description: Skill description
            confidence: Confidence score

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_button_interaction(
            title="Please confirm your intent",
            desc=f"Detected you may want: **{matched_skill}**\n{skill_description}\nConfidence: {confidence:.0%}",
            buttons=[
                {"text": "Confirm", "key": f"confirm:{matched_skill}"},
                {"text": "Cancel", "key": "cancel"},
            ],
        )

        return await self.send_card_to_chat(chat_id, card)

    async def send_error_card(
        self,
        user_id: str,
        error_message: str,
    ) -> Dict:
        """
        Send error notification card.

        Args:
            user_id: Receiver user ID
            error_message: Error message

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title="Operation Failed",
            desc=f"{error_message}",
        )

        return await self.send_card(user_id, card)

    async def send_error_card_to_chat(
        self,
        chat_id: str,
        error_message: str,
    ) -> Dict:
        """
        Send error notification card to group chat.

        Args:
            chat_id: Group chat ID
            error_message: Error message

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title="Operation Failed",
            desc=f"{error_message}",
        )

        return await self.send_card_to_chat(chat_id, card)

    async def send_success_card(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> Dict:
        """
        Send success notification card.

        Args:
            user_id: Receiver user ID
            title: Card title
            message: Success message

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title=title,
            desc=message,
        )

        return await self.send_card(user_id, card)

    async def send_success_card_to_chat(
        self,
        chat_id: str,
        title: str,
        message: str,
    ) -> Dict:
        """
        Send success notification card to group chat.

        Args:
            chat_id: Group chat ID
            title: Card title
            message: Success message

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title=title,
            desc=message,
        )

        return await self.send_card_to_chat(chat_id, card)

    async def send_async_task_accepted(
        self,
        user_id: str,
        task_name: str,
    ) -> Dict:
        """
        Send async task accepted notification.

        Args:
            user_id: Receiver user ID
            task_name: Task name

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title="Task Accepted",
            desc=f"Your **{task_name}** task has started processing.\n\nYou will be notified when it completes. Please wait...",
        )

        return await self.send_card(user_id, card)

    async def send_async_task_accepted_to_chat(
        self,
        chat_id: str,
        task_name: str,
    ) -> Dict:
        """
        Send async task accepted notification to group chat.

        Args:
            chat_id: Group chat ID
            task_name: Task name

        Returns:
            Dict: Send result
        """
        card = LarkCardBuilder.create_text_notice(
            title="Task Accepted",
            desc=f"Your **{task_name}** task has started processing.\n\nYou will be notified when it completes. Please wait...",
        )

        return await self.send_card_to_chat(chat_id, card)

    # ==================== Markdown messages ====================

    async def send_project_overview(
        self,
        user_id: str,
        project_name: str,
        status: str,
        progress: int,
        risks: List[str],
        next_milestone: str,
    ) -> Dict:
        """
        Send project overview Markdown message.

        Args:
            user_id: Receiver user ID
            project_name: Project name
            status: Project status
            progress: Project progress percentage
            risks: Risk list
            next_milestone: Next milestone

        Returns:
            Dict: Send result
        """
        content = f"""# Project Overview: {project_name}

## Basic Info
- **Status**: {status}
- **Progress**: {progress}%

## Risk Alerts
{chr(10).join([f'- {r}' for r in risks]) if risks else 'No current risks'}

## Next Milestone
{next_milestone}
"""
        return await self._client.send_text_message(
            receive_id=user_id,
            text=content,
        )

    async def send_weekly_report(
        self,
        user_id: str,
        project_name: str,
        week_start: str,
        week_end: str,
        progress: int,
        completed_tasks: List[str],
        pending_tasks: List[str],
        risks: List[str],
    ) -> Dict:
        """
        Send weekly report Markdown message.

        Args:
            user_id: Receiver user ID
            project_name: Project name
            week_start: Week start date
            week_end: Week end date
            progress: Overall progress
            completed_tasks: Completed tasks
            pending_tasks: Pending tasks
            risks: Risk list

        Returns:
            Dict: Send result
        """
        content = f"""# Weekly Report: {project_name}
> Period: {week_start} ~ {week_end}

## Overall Progress
**{progress}%**

## Completed This Week
{chr(10).join([f'- {t}' for t in completed_tasks]) if completed_tasks else 'None'}

## Pending Next Week
{chr(10).join([f'- {t}' for t in pending_tasks]) if pending_tasks else 'None'}

## Risk Alerts
{chr(10).join([f'- {r}' for r in risks]) if risks else 'No current risks'}
"""
        return await self._client.send_text_message(
            receive_id=user_id,
            text=content,
        )

    # ==================== Mention helpers ====================

    @staticmethod
    def mention_user(user_id: str) -> str:
        """
        Generate @user tag for Lark messages.

        Args:
            user_id: User open_id

        Returns:
            str: Mention tag string
        """
        return f"<at user_id='{user_id}'></at>"

    @staticmethod
    def mention_all() -> str:
        """
        Generate @all tag for Lark messages.

        Returns:
            str: Mention all tag string
        """
        return "<at user_id='all'></at>"

    @staticmethod
    def format_text_with_mentions(
        text: str,
        mention_users: Optional[List[str]] = None,
        mention_all: bool = False,
    ) -> str:
        """
        Format text with user mentions.

        Args:
            text: Base text content
            mention_users: List of user IDs to mention
            mention_all: Whether to @all

        Returns:
            str: Formatted text with mentions
        """
        mentions = []
        if mention_all:
            mentions.append(LarkService.mention_all())
        if mention_users:
            for user_id in mention_users:
                mentions.append(LarkService.mention_user(user_id))

        if mentions:
            return f"{text}\n{chr(10).join(mentions)}"
        return text


# Global service instance
_lark_service: Optional[LarkService] = None


def get_lark_service() -> LarkService:
    """Get Lark service instance."""
    global _lark_service
    if _lark_service is None:
        _lark_service = LarkService()
    return _lark_service
