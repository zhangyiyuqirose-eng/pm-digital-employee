"""
PM Digital Employee - Lark API Client
PM Digital Employee System - Lark Open Platform API client

Implements Lark Open Platform API calls, authentication (tenant_access_token),
retry logic, and error handling.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LarkError(Exception):
    """Lark API error."""

    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.message = message


class LarkClient:
    """
    Lark Open Platform API client.

    Implements Lark API calls with automatic tenant_access_token management.
    Token TTL is 7200 seconds; refresh 300 seconds before expiry.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        api_domain: Optional[str] = None,
    ) -> None:
        """
        Initialize Lark client.

        Args:
            app_id: Lark app ID
            app_secret: Lark app secret
            api_domain: Lark API domain
        """
        self.app_id = app_id or settings.lark_app_id
        self.app_secret = app_secret or settings.lark_app_secret
        self.api_domain = api_domain or settings.lark_api_domain

        # Token cache
        self._tenant_token: Optional[str] = None
        self._token_expire_time: float = 0

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_tenant_token(self) -> str:
        """
        Get tenant_access_token.

        Auto-caches and refreshes token. TTL is 7200s, refresh 300s early.

        Returns:
            str: tenant_access_token
        """
        # Check cache (refresh 5 min before expiry)
        if self._tenant_token and time.time() < self._token_expire_time - 300:
            return self._tenant_token

        logger.info("Fetching new tenant_access_token")

        client = await self._get_client()
        url = f"{self.api_domain}/open-apis/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        response = await client.post(url, json=payload)
        data = response.json()

        if data.get("code") != 0:
            logger.error(
                "Failed to get tenant_access_token",
                code=data.get("code"),
                msg=data.get("msg"),
            )
            raise LarkError(
                message=f"Failed to get Lark tenant token: {data.get('msg')}",
                code=data.get("code"),
            )

        self._tenant_token = data.get("tenant_access_token")
        expire_seconds = data.get("expire", 7200)
        self._token_expire_time = time.time() + expire_seconds

        logger.info("tenant_access_token refreshed", expire_in=expire_seconds)

        return self._tenant_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.RequestError)),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True,
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Send API request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            params: URL query params

        Returns:
            Dict: Response data
        """
        client = await self._get_client()
        token = await self.get_tenant_token()

        url = f"{self.api_domain}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            result = response.json()

            # Check Lark API error code
            code = result.get("code", -1)
            if code != 0:
                logger.warning(
                    "Lark API returned error",
                    code=code,
                    msg=result.get("msg"),
                    endpoint=endpoint,
                )

            return result

        except httpx.TimeoutException:
            raise LarkError(message="Lark API request timeout")
        except httpx.RequestError as exc:
            raise LarkError(message=f"Lark API request failed: {str(exc)}")

    # ==================== Message APIs ====================

    async def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: Dict[str, Any],
        receive_id_type: str = "open_id",
    ) -> Dict:
        """
        Send message to user or chat.

        Args:
            receive_id: User open_id or chat_id
            msg_type: Message type (text, interactive, etc.)
            content: Message content dict
            receive_id_type: ID type (open_id, chat_id, union_id, email)

        Returns:
            Dict: Response data
        """
        endpoint = f"/open-apis/im/v1/messages?receive_id_type={receive_id_type}"

        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content if isinstance(content, str) else __import__("json").dumps(content),
        }

        return await self.request("POST", endpoint, data=payload)

    async def send_text_message(
        self,
        receive_id: str,
        text: str,
        receive_id_type: str = "open_id",
    ) -> Dict:
        """
        Send text message.

        Args:
            receive_id: User open_id or chat_id
            text: Text content
            receive_id_type: ID type

        Returns:
            Dict: Response data
        """
        content = {"text": text}
        return await self.send_message(
            receive_id=receive_id,
            msg_type="text",
            content=content,
            receive_id_type=receive_id_type,
        )

    async def send_interactive_card(
        self,
        receive_id: str,
        card: Dict[str, Any],
        receive_id_type: str = "open_id",
    ) -> Dict:
        """
        Send interactive card message.

        Args:
            receive_id: User open_id or chat_id
            card: Card JSON (LarkCardBuilder.build() output)
            receive_id_type: ID type

        Returns:
            Dict: Response data
        """
        # 飞书interactive消息的content需要是卡片JSON字符串
        import json
        content = json.dumps(card)
        return await self.send_message(
            receive_id=receive_id,
            msg_type="interactive",
            content=content,
            receive_id_type=receive_id_type,
        )

    async def send_to_chat(
        self,
        chat_id: str,
        msg_type: str,
        content: Dict[str, Any],
    ) -> Dict:
        """
        Send message to group chat.

        Args:
            chat_id: Group chat ID
            msg_type: Message type
            content: Message content

        Returns:
            Dict: Response data
        """
        return await self.send_message(
            receive_id=chat_id,
            msg_type=msg_type,
            content=content,
            receive_id_type="chat_id",
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
            Dict: Response data
        """
        content = {"text": text}
        return await self.send_to_chat(
            chat_id=chat_id,
            msg_type="text",
            content=content,
        )

    # ==================== User APIs ====================

    async def get_user_info(self, user_id: str) -> Dict:
        """
        Get user info by user_id.

        Args:
            user_id: User ID

        Returns:
            Dict: User info
        """
        endpoint = f"/open-apis/contact/v3/users/{user_id}"
        return await self.request("GET", endpoint)

    async def get_user_list(
        self,
        department_id: str = "0",
        page_size: int = 50,
    ) -> List[Dict]:
        """
        Get user list for department.

        Args:
            department_id: Department ID (0 = root)
            page_size: Page size

        Returns:
            List[Dict]: User list
        """
        endpoint = "/open-apis/contact/v3/users/find_by_department"
        params = {
            "department_id": department_id,
            "page_size": page_size,
        }
        result = await self.request("GET", endpoint, params=params)
        return result.get("data", {}).get("items", [])

    # ==================== Chat APIs ====================

    async def get_chat_info(self, chat_id: str) -> Dict:
        """
        Get chat info.

        Args:
            chat_id: Chat ID

        Returns:
            Dict: Chat info
        """
        endpoint = f"/open-apis/im/v1/chats/{chat_id}"
        return await self.request("GET", endpoint)

    async def update_card(
        self,
        message_id: str,
        card: Dict[str, Any],
    ) -> Dict:
        """
        Update an existing interactive card in a message.

        Args:
            message_id: Message ID containing the card
            card: Updated card JSON

        Returns:
            Dict: Response data
        """
        endpoint = f"/open-apis/im/v1/messages/{message_id}"
        content = {
            "type": "template",
            "data": card,
        }
        return await self.request(
            "PUT",
            endpoint,
            data={
                "msg_type": "interactive",
                "content": __import__("json").dumps(content),
            },
        )

    # ==================== v1.3.0新增：文件API ====================

    async def download_file(
        self,
        file_key: str,
    ) -> bytes:
        """
        Download file from Lark.

        API: /open-apis/im/v1/files/{file_key}/download

        Args:
            file_key: Lark file key

        Returns:
            bytes: File content

        Raises:
            LarkError: Download failed
        """
        client = await self._get_client()
        token = await self.get_tenant_token()

        url = f"{self.api_domain}/open-apis/im/v1/files/{file_key}/download"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        logger.info("Downloading file from Lark", file_key=file_key)

        try:
            response = await client.get(url, headers=headers, timeout=60.0)

            if response.status_code != 200:
                logger.error(
                    "File download failed",
                    file_key=file_key,
                    status_code=response.status_code,
                )
                raise LarkError(
                    message=f"File download failed: status {response.status_code}",
                )

            content = response.content
            logger.info(
                "File downloaded successfully",
                file_key=file_key,
                size=len(content),
            )

            return content

        except httpx.TimeoutException:
            logger.error("File download timeout", file_key=file_key)
            raise LarkError(message="File download timeout")
        except httpx.RequestError as exc:
            logger.error("File download request error", file_key=file_key, error=str(exc))
            raise LarkError(message=f"File download request failed: {str(exc)}")

    async def get_file_info(
        self,
        file_key: str,
    ) -> Dict:
        """
        Get file metadata.

        API: /open-apis/im/v1/files/{file_key}

        Args:
            file_key: Lark file key

        Returns:
            Dict: File metadata (name, size, type, etc.)
        """
        endpoint = f"/open-apis/im/v1/files/{file_key}"
        result = await self.request("GET", endpoint)

        if result.get("code") != 0:
            logger.warning(
                "Get file info failed",
                file_key=file_key,
                code=result.get("code"),
                msg=result.get("msg"),
            )
            return {}

        return result.get("data", {})

    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        file_type: str = "stream",
    ) -> Dict:
        """
        Upload file to Lark.

        API: /open-apis/im/v1/files/upload

        Args:
            file_content: File bytes
            file_name: File name
            file_type: File type (stream, image, etc.)

        Returns:
            Dict: Upload result with file_key
        """
        client = await self._get_client()
        token = await self.get_tenant_token()

        url = f"{self.api_domain}/open-apis/im/v1/files/upload"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        files = {
            "file": (file_name, file_content),
        }
        data = {
            "file_type": file_type,
        }

        logger.info("Uploading file to Lark", file_name=file_name)

        try:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60.0,
            )

            result = response.json()

            if result.get("code") != 0:
                logger.error(
                    "File upload failed",
                    file_name=file_name,
                    code=result.get("code"),
                    msg=result.get("msg"),
                )
                raise LarkError(
                    message=f"File upload failed: {result.get('msg')}",
                    code=result.get("code"),
                )

            logger.info(
                "File uploaded successfully",
                file_name=file_name,
                file_key=result.get("data", {}).get("file_key"),
            )

            return result.get("data", {})

        except httpx.TimeoutException:
            raise LarkError(message="File upload timeout")
        except httpx.RequestError as exc:
            raise LarkError(message=f"File upload request failed: {str(exc)}")

    async def download_image(
        self,
        image_key: str,
    ) -> bytes:
        """
        Download image from Lark.

        API: /open-apis/im/v1/images/{image_key}/download

        Args:
            image_key: Lark image key

        Returns:
            bytes: Image content
        """
        client = await self._get_client()
        token = await self.get_tenant_token()

        url = f"{self.api_domain}/open-apis/im/v1/images/{image_key}/download"

        headers = {
            "Authorization": f"Bearer {token}",
        }

        logger.info("Downloading image from Lark", image_key=image_key)

        try:
            response = await client.get(url, headers=headers, timeout=30.0)

            if response.status_code != 200:
                raise LarkError(
                    message=f"Image download failed: status {response.status_code}",
                )

            return response.content

        except httpx.TimeoutException:
            raise LarkError(message="Image download timeout")
        except httpx.RequestError as exc:
            raise LarkError(message=f"Image download request failed: {str(exc)}")


# Global client instance
_lark_client: Optional[LarkClient] = None


def get_lark_client() -> LarkClient:
    """Get Lark client instance."""
    global _lark_client
    if _lark_client is None:
        _lark_client = LarkClient()
    return _lark_client
