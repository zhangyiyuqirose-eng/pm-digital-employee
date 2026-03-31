"""
PM Digital Employee - Idempotency Service
项目经理数字员工系统 - 事件幂等控制服务

基于Redis实现飞书事件幂等处理，防止重复消费。
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class IdempotencyService:
    """
    幂等控制服务.

    基于Redis实现事件幂等处理，防止飞书事件重复消费。
    支持自定义过期时间，默认24小时。
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """
        初始化幂等服务.

        Args:
            redis_client: Redis客户端实例
        """
        self._redis = redis_client
        self._key_prefix = "idempotency:lark:"
        self._default_ttl = 24 * 60 * 60  # 24小时

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

    async def check_and_lock(
        self,
        event_id: str,
        event_type: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        检查事件是否已处理，并加锁.

        使用Redis SETNX实现原子性检查+加锁。

        Args:
            event_id: 事件ID
            event_type: 事件类型
            ttl: 过期时间（秒）

        Returns:
            bool: True表示首次处理，False表示已处理
        """
        redis_client = await self._get_redis()
        key = self._build_key(event_id, event_type)
        ttl = ttl or self._default_ttl

        # 使用SETNX原子操作
        lock_data = {
            "event_id": event_id,
            "event_type": event_type,
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "status": "processing",
        }

        result = await redis_client.set(
            key,
            json.dumps(lock_data),
            nx=True,  # 仅当key不存在时设置
            ex=ttl,
        )

        if result:
            logger.debug(
                "Event locked for processing",
                event_id=event_id,
                event_type=event_type,
            )
            return True

        logger.info(
            "Event already processed, skipping",
            event_id=event_id,
            event_type=event_type,
        )
        return False

    async def mark_completed(
        self,
        event_id: str,
        event_type: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        标记事件处理完成.

        Args:
            event_id: 事件ID
            event_type: 事件类型
            result: 处理结果

        Returns:
            bool: 是否成功标记
        """
        redis_client = await self._get_redis()
        key = self._build_key(event_id, event_type)

        # 获取现有数据
        existing = await redis_client.get(key)
        if not existing:
            logger.warning(
                "Event lock not found when marking completed",
                event_id=event_id,
            )
            return False

        # 更新状态
        lock_data = json.loads(existing)
        lock_data["status"] = "completed"
        lock_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        if result:
            lock_data["result"] = result

        await redis_client.set(key, json.dumps(lock_data), ex=self._default_ttl)

        logger.debug(
            "Event marked as completed",
            event_id=event_id,
            event_type=event_type,
        )
        return True

    async def mark_failed(
        self,
        event_id: str,
        event_type: str,
        error_message: str,
    ) -> bool:
        """
        标记事件处理失败.

        Args:
            event_id: 事件ID
            event_type: 事件类型
            error_message: 错误信息

        Returns:
            bool: 是否成功标记
        """
        redis_client = await self._get_redis()
        key = self._build_key(event_id, event_type)

        existing = await redis_client.get(key)
        if not existing:
            return False

        lock_data = json.loads(existing)
        lock_data["status"] = "failed"
        lock_data["failed_at"] = datetime.now(timezone.utc).isoformat()
        lock_data["error_message"] = error_message

        await redis_client.set(key, json.dumps(lock_data), ex=self._default_ttl)

        logger.warning(
            "Event marked as failed",
            event_id=event_id,
            error_message=error_message,
        )
        return True

    async def get_event_status(
        self,
        event_id: str,
        event_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取事件处理状态.

        Args:
            event_id: 事件ID
            event_type: 事件类型

        Returns:
            Optional[Dict]: 事件状态信息
        """
        redis_client = await self._get_redis()
        key = self._build_key(event_id, event_type)

        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    async def is_processed(
        self,
        event_id: str,
        event_type: str,
    ) -> bool:
        """
        检查事件是否已处理.

        Args:
            event_id: 事件ID
            event_type: 事件类型

        Returns:
            bool: 是否已处理
        """
        status = await self.get_event_status(event_id, event_type)
        if status:
            return status.get("status") in ("completed", "processing")
        return False

    async def clear_event(
        self,
        event_id: str,
        event_type: str,
    ) -> bool:
        """
        清除事件记录（用于测试或特殊场景）.

        Args:
            event_id: 事件ID
            event_type: 事件类型

        Returns:
            bool: 是否成功清除
        """
        redis_client = await self._get_redis()
        key = self._build_key(event_id, event_type)

        result = await redis_client.delete(key)
        return result > 0

    def _build_key(self, event_id: str, event_type: str) -> str:
        """
        构建Redis key.

        Args:
            event_id: 事件ID
            event_type: 事件类型

        Returns:
            str: Redis key
        """
        return f"{self._key_prefix}{event_type}:{event_id}"


class MessageIdempotencyService:
    """
    消息幂等控制服务.

    专门处理飞书消息事件的幂等。
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """初始化消息幂等服务."""
        self._service = IdempotencyService(redis_client)

    async def check_message(
        self,
        message_id: str,
    ) -> bool:
        """
        检查消息是否已处理.

        Args:
            message_id: 消息ID

        Returns:
            bool: True表示首次处理
        """
        return await self._service.check_and_lock(
            event_id=message_id,
            event_type="message",
        )

    async def mark_message_completed(
        self,
        message_id: str,
        response_message_id: Optional[str] = None,
    ) -> bool:
        """
        标记消息处理完成.

        Args:
            message_id: 消息ID
            response_message_id: 回复消息ID

        Returns:
            bool: 是否成功标记
        """
        return await self._service.mark_completed(
            event_id=message_id,
            event_type="message",
            result={"response_message_id": response_message_id},
        )


class CardCallbackIdempotencyService:
    """
    卡片回调幂等控制服务.

    专门处理飞书卡片回调的幂等。
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """初始化卡片回调幂等服务."""
        self._service = IdempotencyService(redis_client)

    async def check_callback(
        self,
        open_message_id: str,
        action_value: Dict[str, Any],
    ) -> bool:
        """
        检查卡片回调是否已处理.

        使用消息ID+action_value作为唯一标识。

        Args:
            open_message_id: 消息ID
            action_value: 动作值

        Returns:
            bool: True表示首次处理
        """
        # 构建唯一标识
        action_key = json.dumps(action_value, sort_keys=True)
        callback_id = f"{open_message_id}:{action_key}"

        return await self._service.check_and_lock(
            event_id=callback_id,
            event_type="card_callback",
            ttl=60 * 60,  # 1小时，卡片回调时效较短
        )

    async def mark_callback_completed(
        self,
        open_message_id: str,
        action_value: Dict[str, Any],
        result_card_id: Optional[str] = None,
    ) -> bool:
        """
        标记卡片回调处理完成.

        Args:
            open_message_id: 消息ID
            action_value: 动作值
            result_card_id: 结果卡片ID

        Returns:
            bool: 是否成功标记
        """
        action_key = json.dumps(action_value, sort_keys=True)
        callback_id = f"{open_message_id}:{action_key}"

        return await self._service.mark_completed(
            event_id=callback_id,
            event_type="card_callback",
            result={"result_card_id": result_card_id},
        )


# 全局幂等服务实例
_idempotency_service: Optional[IdempotencyService] = None
_message_idempotency_service: Optional[MessageIdempotencyService] = None
_card_callback_idempotency_service: Optional[CardCallbackIdempotencyService] = None


def get_idempotency_service() -> IdempotencyService:
    """获取幂等服务实例."""
    global _idempotency_service
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService()
    return _idempotency_service


def get_message_idempotency_service() -> MessageIdempotencyService:
    """获取消息幂等服务实例."""
    global _message_idempotency_service
    if _message_idempotency_service is None:
        _message_idempotency_service = MessageIdempotencyService()
    return _message_idempotency_service


def get_card_callback_idempotency_service() -> CardCallbackIdempotencyService:
    """获取卡片回调幂等服务实例."""
    global _card_callback_idempotency_service
    if _card_callback_idempotency_service is None:
        _card_callback_idempotency_service = CardCallbackIdempotencyService()
    return _card_callback_idempotency_service