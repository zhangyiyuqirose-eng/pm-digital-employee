"""
PM Digital Employee - Lark API Client
项目经理数字员工系统 - 飞书API统一客户端封装

实现飞书开放平台API调用、认证、重试、错误处理。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LarkError(Exception):
    """飞书API异常."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message


class LarkClient:
    """
    飞书API统一客户端.

    实现飞书开放平台API调用、认证、重试、错误处理。
    支持tenant_access_token自动获取和缓存。
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        api_domain: Optional[str] = None,
    ) -> None:
        """
        初始化飞书客户端.

        Args:
            app_id: 飞书应用ID
            app_secret: 飞书应用密钥
            api_domain: API域名
        """
        self.app_id = app_id or settings.lark_app_id
        self.app_secret = app_secret or settings.lark_app_secret
        self.api_domain = api_domain or settings.lark_api_domain

        # Token缓存
        self._tenant_access_token: Optional[str] = None
        self._token_expire_time: float = 0

        # HTTP客户端
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_tenant_access_token(self) -> str:
        """
        获取tenant_access_token.

        自动缓存和刷新Token。

        Returns:
            str: tenant_access_token
        """
        # 检查缓存是否有效（提前5分钟刷新）
        if self._tenant_access_token and time.time() < self._token_expire_time - 300:
            return self._tenant_access_token

        logger.info("Fetching new tenant_access_token")

        client = await self._get_client()
        url = f"{self.api_domain}/open-apis/auth/v3/tenant_access_token/internal/"

        response = await client.post(
            url,
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret,
            },
        )

        data = response.json()

        if data.get("code") != 0:
            logger.error(
                "Failed to get tenant_access_token",
                code=data.get("code"),
                message=data.get("msg"),
            )
            raise LarkError(
                message=f"获取飞书Token失败: {data.get('msg')}",
                code=data.get("code"),
            )

        self._tenant_access_token = data.get("tenant_access_token")
        expire_seconds = data.get("expire", 7200)
        self._token_expire_time = time.time() + expire_seconds

        logger.info("tenant_access_token refreshed", expire_in=expire_seconds)

        return self._tenant_access_token

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        发送API请求.

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求体数据
            params: URL参数

        Returns:
            Dict: 响应数据
        """
        client = await self._get_client()
        token = await self.get_tenant_access_token()

        url = f"{self.api_domain}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            result = response.json()
            return result

        except httpx.TimeoutException:
            raise LarkError(message="飞书API请求超时")
        except httpx.RequestError as exc:
            raise LarkError(message=f"飞书API请求失败: {str(exc)}")

    # ==================== 消息相关API ====================

    async def send_text_message(
        self,
        receive_id: str,
        receive_id_type: str,
        text: str,
    ) -> Dict:
        """
        发送文本消息.

        Args:
            receive_id: 接收者ID
            receive_id_type: 接收者类型（open_id/user_id/chat_id）
            text: 文本内容

        Returns:
            Dict: 响应数据
        """
        import json
        return await self.request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            data={
                "receive_id": receive_id,
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )

    async def send_card_message(
        self,
        receive_id: str,
        receive_id_type: str,
        card: Dict,
    ) -> Dict:
        """
        发送卡片消息.

        Args:
            receive_id: 接收者ID
            receive_id_type: 接收者类型
            card: 卡片内容

        Returns:
            Dict: 响应数据
        """
        import json

        return await self.request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            data={
                "receive_id": receive_id,
                "msg_type": "interactive",
                "content": json.dumps(card),
            },
        )

    async def reply_message(
        self,
        message_id: str,
        text: str,
    ) -> Dict:
        """
        回复消息.

        Args:
            message_id: 原消息ID
            text: 消息内容

        Returns:
            Dict: 响应数据
        """
        import json
        return await self.request(
            "POST",
            f"/open-apis/im/v1/messages/{message_id}/reply",
            data={
                "msg_type": "text",
                "content": json.dumps({"text": text}),
            },
        )

    # ==================== 用户相关API ====================

    async def get_user_info(self, user_id: str, user_id_type: str = "open_id") -> Dict:
        """
        获取用户信息.

        Args:
            user_id: 用户ID
            user_id_type: 用户ID类型

        Returns:
            Dict: 用户信息
        """
        result = await self.request(
            "GET",
            f"/open-apis/contact/v3/users/{user_id}",
            params={"user_id_type": user_id_type},
        )
        return result.get("data", {}).get("user", {})

    # ==================== 群相关API ====================

    async def get_chat_info(self, chat_id: str) -> Dict:
        """
        获取群信息.

        Args:
            chat_id: 群ID

        Returns:
            Dict: 群信息
        """
        result = await self.request(
            "GET",
            f"/open-apis/im/v1/chats/{chat_id}",
        )
        return result.get("data", {})


# 全局客户端实例
_lark_client: Optional[LarkClient] = None


def get_lark_client() -> LarkClient:
    """获取飞书客户端实例."""
    global _lark_client
    if _lark_client is None:
        _lark_client = LarkClient()
    return _lark_client