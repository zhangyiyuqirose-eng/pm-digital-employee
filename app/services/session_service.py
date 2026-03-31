"""
PM Digital Employee - Session Service
项目经理数字员工系统 - 会话管理服务

管理用户会话状态、会话持久化、会话清理。
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models.conversation import ConversationSession, ConversationMessage

logger = get_logger(__name__)


class SessionService:
    """
    会话管理服务.

    管理用户会话状态、会话持久化、会话清理。
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        """
        初始化会话服务.

        Args:
            redis_client: Redis客户端
        """
        self._redis = redis_client
        self._key_prefix = "session:"
        self._session_ttl = 30 * 60  # 30分钟会话过期
        self._message_ttl = 7 * 24 * 60 * 60  # 消息保留7天

    async def _get_redis(self) -> redis.Redis:
        """获取Redis客户端."""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                decode_responses=True,
            )
        return self._redis

    async def create_session(
        self,
        user_id: str,
        chat_id: str,
        chat_type: str = "p2p",
        project_id: Optional[uuid.UUID] = None,
    ) -> ConversationSession:
        """
        创建新会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID
            chat_type: 会话类型
            project_id: 项目ID

        Returns:
            ConversationSession: 会话对象
        """
        session = ConversationSession(
            id=uuid.uuid4(),
            user_id=user_id,
            chat_id=chat_id,
            chat_type=chat_type,
            project_id=project_id,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # 保存到Redis
        await self._save_session(session)

        # 创建用户-会话映射
        redis_client = await self._get_redis()
        mapping_key = f"session:mapping:{user_id}:{chat_id}"
        await redis_client.set(
            mapping_key,
            str(session.id),
            ex=self._session_ttl,
        )

        logger.info(
            "Session created",
            session_id=str(session.id),
            user_id=user_id,
            chat_id=chat_id,
        )

        return session

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[ConversationSession]:
        """
        获取会话.

        Args:
            session_id: 会话ID

        Returns:
            Optional[ConversationSession]: 会话对象
        """
        redis_client = await self._get_redis()
        key = self._build_key(session_id)

        import json
        data = await redis_client.get(key)

        if data:
            session_dict = json.loads(data)
            return ConversationSession.model_validate(session_dict)

        return None

    async def get_active_session(
        self,
        user_id: str,
        chat_id: str,
    ) -> Optional[ConversationSession]:
        """
        获取活跃会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID

        Returns:
            Optional[ConversationSession]: 活跃会话
        """
        redis_client = await self._get_redis()
        mapping_key = f"session:mapping:{user_id}:{chat_id}"

        session_id = await redis_client.get(mapping_key)
        if session_id:
            return await self.get_session(session_id)

        return None

    async def get_or_create_session(
        self,
        user_id: str,
        chat_id: str,
        chat_type: str = "p2p",
        project_id: Optional[uuid.UUID] = None,
    ) -> ConversationSession:
        """
        获取或创建会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID
            chat_type: 会话类型
            project_id: 项目ID

        Returns:
            ConversationSession: 会话对象
        """
        existing = await self.get_active_session(user_id, chat_id)
        if existing:
            # 更新会话过期时间
            await self._refresh_session(existing)
            return existing

        return await self.create_session(user_id, chat_id, chat_type, project_id)

    async def update_session(
        self,
        session: ConversationSession,
    ) -> None:
        """
        更新会话.

        Args:
            session: 会话对象
        """
        session.updated_at = datetime.now(timezone.utc)
        await self._save_session(session)

    async def end_session(
        self,
        session_id: str,
    ) -> bool:
        """
        结束会话.

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        redis_client = await self._get_redis()
        key = self._build_key(session_id)

        result = await redis_client.delete(key)

        logger.info(
            "Session ended",
            session_id=session_id,
        )

        return result > 0

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """
        添加消息到会话.

        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system）
            content: 消息内容
            metadata: 元数据

        Returns:
            ConversationMessage: 消息对象
        """
        message = ConversationMessage(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            role=role,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
        )

        # 保存消息
        redis_client = await self._get_redis()
        message_key = f"session:messages:{session_id}"

        import json
        message_data = json.dumps({
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat(),
        })

        # 使用Redis List存储消息历史
        await redis_client.rpush(message_key, message_data)
        await redis_client.expire(message_key, self._message_ttl)

        # 更新会话
        session = await self.get_session(session_id)
        if session:
            await self.update_session(session)

        return message

    async def get_messages(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取会话消息历史.

        Args:
            session_id: 会话ID
            limit: 最大消息数

        Returns:
            List: 消息列表
        """
        redis_client = await self._get_redis()
        message_key = f"session:messages:{session_id}"

        # 获取最近的N条消息
        messages_data = await redis_client.lrange(
            message_key,
            -limit,
            -1,
        )

        import json
        messages = []
        for data in messages_data:
            messages.append(json.loads(data))

        return messages

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        获取对话历史（用于LLM上下文）.

        Args:
            session_id: 会话ID
            limit: 最大消息数

        Returns:
            List: 对话历史
        """
        messages = await self.get_messages(session_id, limit)

        return [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            }
            for msg in messages
        ]

    async def clear_messages(
        self,
        session_id: str,
    ) -> bool:
        """
        清除会话消息.

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功
        """
        redis_client = await self._get_redis()
        message_key = f"session:messages:{session_id}"

        await redis_client.delete(message_key)
        return True

    async def _save_session(
        self,
        session: ConversationSession,
    ) -> None:
        """
        保存会话到Redis.

        Args:
            session: 会话对象
        """
        redis_client = await self._get_redis()
        key = self._build_key(str(session.id))

        import json
        data = json.dumps(
            session.model_dump(exclude_none=True),
            ensure_ascii=False,
            default=str,
        )

        await redis_client.set(key, data, ex=self._session_ttl)

    async def _refresh_session(
        self,
        session: ConversationSession,
    ) -> None:
        """
        刷新会话过期时间.

        Args:
            session: 会话对象
        """
        redis_client = await self._get_redis()
        key = self._build_key(str(session.id))
        await redis_client.expire(key, self._session_ttl)

        # 同时刷新映射
        mapping_key = f"session:mapping:{session.user_id}:{session.chat_id}"
        await redis_client.expire(mapping_key, self._session_ttl)

    def _build_key(self, session_id: str) -> str:
        """构建Redis key."""
        return f"{self._key_prefix}{session_id}"


# 全局会话服务实例
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """获取会话服务实例."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service