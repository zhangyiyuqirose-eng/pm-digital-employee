"""
PM Digital Employee - Event Bus
项目经理数字员工系统 - 事件总线

实现事件发布订阅模式，支持异步事件处理。
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """事件类型."""

    # 消息事件
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"

    # 任务事件
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"

    # 风险事件
    RISK_DETECTED = "risk.detected"
    RISK_UPDATED = "risk.updated"
    RISK_ESCALATED = "risk.escalated"

    # 项目事件
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_STATUS_CHANGED = "project.status_changed"

    # Skill事件
    SKILL_EXECUTED = "skill.executed"
    SKILL_FAILED = "skill.failed"

    # 成本事件
    COST_EXCEEDED = "cost.exceeded"
    COST_WARNING = "cost.warning"

    # 里程碑事件
    MILESTONE_DUE = "milestone.due"
    MILESTONE_COMPLETED = "milestone.completed"

    # 审批事件
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"


@dataclass
class Event:
    """
    事件对象.

    封装事件数据。
    """

    event_type: EventType
    event_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "payload": self.payload,
            "metadata": self.metadata,
        }


class EventHandler(ABC):
    """
    事件处理器基类.
    """

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """
        处理事件.

        Args:
            event: 事件对象
        """
        pass

    @property
    @abstractmethod
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        pass


class EventBus:
    """
    事件总线.

    实现事件发布订阅模式。
    """

    def __init__(self) -> None:
        """初始化事件总线."""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def subscribe(
        self,
        handler: EventHandler,
    ) -> None:
        """
        订阅事件.

        Args:
            handler: 事件处理器
        """
        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []

            self._handlers[event_type].append(handler)

            logger.debug(
                "Handler subscribed to event",
                handler=handler.__class__.__name__,
                event_type=event_type.value,
            )

    def subscribe_callable(
        self,
        event_type: EventType,
        handler: Callable,
    ) -> None:
        """
        订阅事件（使用函数）.

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []

        self._async_handlers[event_type].append(handler)

    def unsubscribe(
        self,
        handler: EventHandler,
    ) -> None:
        """
        取消订阅.

        Args:
            handler: 事件处理器
        """
        for event_type in handler.event_types:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass

    async def publish(
        self,
        event: Event,
    ) -> None:
        """
        发布事件.

        Args:
            event: 事件对象
        """
        logger.debug(
            "Event published",
            event_type=event.event_type.value,
            event_id=event.event_id,
        )

        # 放入队列异步处理
        await self._event_queue.put(event)

    async def publish_and_wait(
        self,
        event: Event,
    ) -> None:
        """
        发布事件并等待处理完成.

        Args:
            event: 事件对象
        """
        await self._dispatch(event)

    async def _dispatch(
        self,
        event: Event,
    ) -> None:
        """
        分发事件到处理器.

        Args:
            event: 事件对象
        """
        event_type = event.event_type

        # 调用注册的处理器
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    "Event handler error",
                    handler=handler.__class__.__name__,
                    event_type=event_type.value,
                    error=str(e),
                )

        # 调用注册的函数处理器
        async_handlers = self._async_handlers.get(event_type, [])
        for handler in async_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    "Async event handler error",
                    event_type=event_type.value,
                    error=str(e),
                )

    async def start(self) -> None:
        """启动事件处理循环."""
        self._running = True
        logger.info("Event bus started")

        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Event bus error", error=str(e))

    async def stop(self) -> None:
        """停止事件处理循环."""
        self._running = False
        logger.info("Event bus stopped")

    def create_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        创建事件.

        Args:
            event_type: 事件类型
            payload: 事件载荷
            source: 事件来源
            metadata: 元数据

        Returns:
            Event: 事件对象
        """
        import uuid

        return Event(
            event_type=event_type,
            event_id=str(uuid.uuid4()),
            source=source,
            payload=payload,
            metadata=metadata or {},
        )


# 全局事件总线实例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取事件总线实例."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def subscribe(handler: EventHandler) -> None:
    """便捷函数：订阅事件."""
    bus = get_event_bus()
    bus.subscribe(handler)


async def publish(event: Event) -> None:
    """便捷函数：发布事件."""
    bus = get_event_bus()
    await bus.publish(event)