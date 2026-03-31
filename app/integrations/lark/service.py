"""
PM Digital Employee - Lark Service
项目经理数字员工系统 - 飞书业务服务

封装飞书常用业务操作：消息发送、文件处理、用户信息获取等。
"""

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import ErrorCode, LarkError
from app.core.logging import get_logger
from app.integrations.lark.client import LarkClient, get_lark_client
from app.integrations.lark.schemas import LarkCardBuilder

logger = get_logger(__name__)


class LarkService:
    """
    飞书业务服务.

    封装飞书常用业务操作。
    """

    def __init__(self, client: Optional[LarkClient] = None) -> None:
        """
        初始化飞书服务.

        Args:
            client: 飞书客户端实例
        """
        self._client = client or get_lark_client()

    @property
    def client(self) -> LarkClient:
        """获取飞书客户端."""
        return self._client

    # ==================== 消息发送 ====================

    async def send_text(
        self,
        receive_id: str,
        text: str,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送文本消息.

        Args:
            receive_id: 接收者ID（用户OpenID或群ID）
            text: 文本内容
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        content = json.dumps({"text": text})
        return await self._client.send_text_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            content=content,
        )

    async def send_markdown(
        self,
        receive_id: str,
        markdown: str,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送Markdown消息.

        Args:
            receive_id: 接收者ID
            markdown: Markdown内容
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        content = json.dumps({"zh_cn": {"content": markdown}})
        return await self._client.send_text_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            content=content,
            msg_type="post",
        )

    async def send_card(
        self,
        receive_id: str,
        card: Dict[str, Any],
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送交互式卡片.

        Args:
            receive_id: 接收者ID
            card: 卡片内容
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        return await self._client.send_card_message(
            receive_id=receive_id,
            receive_id_type=receive_id_type,
            card=card,
        )

    async def reply_text(
        self,
        message_id: str,
        text: str,
    ) -> Dict:
        """
        回复文本消息.

        Args:
            message_id: 原消息ID
            text: 回复内容

        Returns:
            Dict: 发送结果
        """
        content = json.dumps({"text": text})
        return await self._client.reply_message(
            message_id=message_id,
            content=content,
        )

    async def reply_card(
        self,
        message_id: str,
        card: Dict[str, Any],
    ) -> Dict:
        """
        回复卡片消息.

        Args:
            message_id: 原消息ID
            card: 卡片内容

        Returns:
            Dict: 发送结果
        """
        content = json.dumps(card)
        return await self._client.reply_message(
            message_id=message_id,
            content=content,
            msg_type="interactive",
        )

    # ==================== 用户信息 ====================

    async def get_user_info(self, open_id: str) -> Dict:
        """
        获取用户信息.

        Args:
            open_id: 用户OpenID

        Returns:
            Dict: 用户信息
        """
        return await self._client.get_user_info(open_id)

    async def get_user_name(self, open_id: str) -> str:
        """
        获取用户姓名.

        Args:
            open_id: 用户OpenID

        Returns:
            str: 用户姓名
        """
        user = await self.get_user_info(open_id)
        return user.get("name", open_id)

    # ==================== 群信息 ====================

    async def get_chat_info(self, chat_id: str) -> Dict:
        """
        获取群信息.

        Args:
            chat_id: 群ID

        Returns:
            Dict: 群信息
        """
        return await self._client.get_chat_info(chat_id)

    async def get_chat_members(self, chat_id: str) -> List[Dict]:
        """
        获取群成员列表.

        Args:
            chat_id: 群ID

        Returns:
            List[Dict]: 成员列表
        """
        return await self._client.get_chat_members(chat_id)

    # ==================== 卡片构建 ====================

    def create_card(self) -> LarkCardBuilder:
        """
        创建卡片构建器.

        Returns:
            LarkCardBuilder: 卡片构建器
        """
        return LarkCardBuilder()

    async def send_clarification_card(
        self,
        receive_id: str,
        matched_skill: str,
        skill_description: str,
        confidence: float,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送意图澄清卡片.

        Args:
            receive_id: 接收者ID
            matched_skill: 匹配的Skill名称
            skill_description: Skill描述
            confidence: 置信度
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        card = (
            self.create_card()
            .set_header("请确认您的意图", "blue")
            .add_markdown(f"检测到您可能想要：**{matched_skill}**\n\n{skill_description}\n\n置信度: {confidence:.0%}")
            .add_divider()
            .add_action(
                [
                    LarkCardBuilder.create_button(
                        "确认执行",
                        {"action": "confirm", "skill": matched_skill},
                        "primary",
                    ),
                    LarkCardBuilder.create_button(
                        "取消",
                        {"action": "cancel"},
                        "default",
                    ),
                ]
            )
            .build()
        )

        return await self.send_card(receive_id, card, receive_id_type)

    async def send_error_card(
        self,
        receive_id: str,
        error_message: str,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送错误提示卡片.

        Args:
            receive_id: 接收者ID
            error_message: 错误信息
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        card = (
            self.create_card()
            .set_header("操作失败", "red")
            .add_markdown(f"❌ {error_message}")
            .build()
        )

        return await self.send_card(receive_id, card, receive_id_type)

    async def send_success_card(
        self,
        receive_id: str,
        title: str,
        message: str,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送成功提示卡片.

        Args:
            receive_id: 接收者ID
            title: 标题
            message: 消息内容
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        card = (
            self.create_card()
            .set_header(title, "green")
            .add_markdown(f"✅ {message}")
            .build()
        )

        return await self.send_card(receive_id, card, receive_id_type)

    async def send_async_task_accepted(
        self,
        receive_id: str,
        task_name: str,
        receive_id_type: str = "chat_id",
    ) -> Dict:
        """
        发送异步任务已受理提示.

        Args:
            receive_id: 接收者ID
            task_name: 任务名称
            receive_id_type: 接收者类型

        Returns:
            Dict: 发送结果
        """
        card = (
            self.create_card()
            .set_header("任务已受理", "blue")
            .add_markdown(f"⏳ 您的 **{task_name}** 任务已开始处理\n\n处理完成后会主动通知您，请稍候...")
            .build()
        )

        return await self.send_card(receive_id, card, receive_id_type)


# 全局服务实例
_lark_service: Optional[LarkService] = None


def get_lark_service() -> LarkService:
    """获取飞书服务实例."""
    global _lark_service
    if _lark_service is None:
        _lark_service = LarkService()
    return _lark_service