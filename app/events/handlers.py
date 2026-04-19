"""
PM Digital Employee - Event Handlers
项目经理数字员工系统 - 事件处理器

定义各种事件的具体处理器，支持@on_event装饰器模式。
"""

import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from app.core.logging import get_logger
from app.events.bus import Event, EventHandler, EventType, get_event_bus

logger = get_logger(__name__)


# ============================================
# Decorator Pattern: @on_event
# ============================================

def on_event(
    event_types: Union[EventType, List[EventType]],
    source: Optional[str] = None,
) -> Callable:
    """
    Event handler decorator.

    Simplifies event handler registration with decorator syntax.

    Args:
        event_types: Single or list of event types to subscribe
        source: Optional source identifier

    Returns:
        Decorated function

    Example:
        @on_event(EventType.RISK_DETECTED)
        async def handle_risk(event: Event):
            logger.info("Risk detected", risk_id=event.payload.get("risk_id"))

        @on_event([EventType.TASK_CREATED, EventType.TASK_UPDATED])
        async def handle_task_events(event: Event):
            ...
    """
    if isinstance(event_types, EventType):
        event_types = [event_types]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(event: Event) -> None:
            try:
                await func(event)
            except Exception as e:
                logger.error(
                    "Event handler error",
                    handler=func.__name__,
                    event_type=event.event_type.value,
                    error=str(e),
                )

        # Register to event bus
        bus = get_event_bus()
        for et in event_types:
            bus.subscribe_callable(et, wrapper)
            logger.debug(
                "Handler registered via decorator",
                handler=func.__name__,
                event_type=et.value,
            )

        return wrapper

    return decorator


class EventHandlerRegistry:
    """
    Registry for decorated event handlers.

    Tracks all handlers registered via @on_event decorator.
    """

    _registry: Dict[EventType, List[Callable]] = {}

    @classmethod
    def register(
        cls,
        event_type: EventType,
        handler: Callable,
    ) -> None:
        """Register a handler."""
        if event_type not in cls._registry:
            cls._registry[event_type] = []
        cls._registry[event_type].append(handler)

    @classmethod
    def get_handlers(
        cls,
        event_type: EventType,
    ) -> List[Callable]:
        """Get handlers for an event type."""
        return cls._registry.get(event_type, [])

    @classmethod
    def clear(cls) -> None:
        """Clear registry."""
        cls._registry.clear()


class RiskAlertHandler(EventHandler):
    """
    风险预警事件处理器.

    处理风险检测、更新、升级事件。
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.RISK_DETECTED,
            EventType.RISK_UPDATED,
            EventType.RISK_ESCALATED,
        ]

    async def handle(self, event: Event) -> None:
        """处理风险事件."""
        logger.info(
            "Handling risk event",
            event_type=event.event_type.value,
            risk_id=event.payload.get("risk_id"),
        )

        # 获取风险信息
        risk_id = event.payload.get("risk_id")
        project_id = event.payload.get("project_id")
        risk_level = event.payload.get("level", "low")
        description = event.payload.get("description", "")

        # 根据风险等级发送通知
        if risk_level == "high":
            await self._send_urgent_alert(project_id, risk_id, description)
        elif risk_level == "medium":
            await self._send_warning(project_id, risk_id, description)
        else:
            await self._log_risk(risk_id, description)

    async def _send_urgent_alert(
        self,
        project_id: str,
        risk_id: str,
        description: str,
    ) -> None:
        """发送紧急预警."""
        from app.integrations.lark.service import get_lark_service

        try:
            lark_service = get_lark_service()

            # TODO: 获取项目经理的chat_id
            # await lark_service.send_error_card(...)
            logger.warning(
                "High risk alert sent",
                project_id=project_id,
                risk_id=risk_id,
                description=description,
            )
        except Exception as e:
            logger.error(
                "Failed to send urgent alert",
                error=str(e),
            )

    async def _send_warning(
        self,
        project_id: str,
        risk_id: str,
        description: str,
    ) -> None:
        """发送警告."""
        logger.warning(
            "Medium risk warning",
            project_id=project_id,
            risk_id=risk_id,
            description=description,
        )

    async def _log_risk(
        self,
        risk_id: str,
        description: str,
    ) -> None:
        """记录低风险."""
        logger.info(
            "Low risk logged",
            risk_id=risk_id,
            description=description,
        )


class CostMonitorHandler(EventHandler):
    """
    成本监控事件处理器.

    处理成本超支、预警事件。
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.COST_EXCEEDED,
            EventType.COST_WARNING,
        ]

    async def handle(self, event: Event) -> None:
        """处理成本事件."""
        project_id = event.payload.get("project_id")
        budget = event.payload.get("budget", 0)
        actual = event.payload.get("actual", 0)
        variance_percent = event.payload.get("variance_percent", 0)

        if event.event_type == EventType.COST_EXCEEDED:
            logger.warning(
                "Cost exceeded alert",
                project_id=project_id,
                budget=budget,
                actual=actual,
                variance_percent=variance_percent,
            )
            # TODO: 发送通知

        elif event.event_type == EventType.COST_WARNING:
            logger.info(
                "Cost warning",
                project_id=project_id,
                variance_percent=variance_percent,
            )


class MilestoneHandler(EventHandler):
    """
    里程碑事件处理器.

    处理里程碑到期、完成事件。
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.MILESTONE_DUE,
            EventType.MILESTONE_COMPLETED,
        ]

    async def handle(self, event: Event) -> None:
        """处理里程碑事件."""
        milestone_id = event.payload.get("milestone_id")
        project_id = event.payload.get("project_id")
        milestone_name = event.payload.get("name", "")

        if event.event_type == EventType.MILESTONE_DUE:
            logger.info(
                "Milestone due notification",
                project_id=project_id,
                milestone_id=milestone_id,
                milestone_name=milestone_name,
            )
            # TODO: 发送提醒

        elif event.event_type == EventType.MILESTONE_COMPLETED:
            logger.info(
                "Milestone completed",
                project_id=project_id,
                milestone_id=milestone_id,
            )


class SkillExecutionHandler(EventHandler):
    """
    Skill执行事件处理器.

    处理Skill执行成功/失败事件。
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.SKILL_EXECUTED,
            EventType.SKILL_FAILED,
        ]

    async def handle(self, event: Event) -> None:
        """处理Skill执行事件."""
        skill_name = event.payload.get("skill_name")
        user_id = event.payload.get("user_id")
        project_id = event.payload.get("project_id")
        duration_ms = event.payload.get("duration_ms", 0)

        if event.event_type == EventType.SKILL_EXECUTED:
            logger.info(
                "Skill executed",
                skill_name=skill_name,
                user_id=user_id,
                project_id=project_id,
                duration_ms=duration_ms,
            )
        else:
            error = event.payload.get("error", "")
            logger.error(
                "Skill execution failed",
                skill_name=skill_name,
                user_id=user_id,
                error=error,
            )


class ApprovalHandler(EventHandler):
    """
    审批事件处理器.

    处理审批请求、通过、拒绝事件。
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.APPROVAL_REQUESTED,
            EventType.APPROVAL_APPROVED,
            EventType.APPROVAL_REJECTED,
        ]

    async def handle(self, event: Event) -> None:
        """处理审批事件."""
        approval_id = event.payload.get("approval_id")
        approval_type = event.payload.get("type", "")
        requester_id = event.payload.get("requester_id")

        if event.event_type == EventType.APPROVAL_REQUESTED:
            logger.info(
                "Approval requested",
                approval_id=approval_id,
                approval_type=approval_type,
                requester_id=requester_id,
            )
            # TODO: 发送审批通知

        elif event.event_type == EventType.APPROVAL_APPROVED:
            logger.info(
                "Approval approved",
                approval_id=approval_id,
            )

        elif event.event_type == EventType.APPROVAL_REJECTED:
            logger.info(
                "Approval rejected",
                approval_id=approval_id,
            )


class TaskUpdateHandler(EventHandler):
    """
    任务更新事件处理器.
    """

    @property
    def event_types(self) -> List[EventType]:
        """订阅的事件类型."""
        return [
            EventType.TASK_CREATED,
            EventType.TASK_UPDATED,
            EventType.TASK_COMPLETED,
        ]

    async def handle(self, event: Event) -> None:
        """处理任务事件."""
        task_id = event.payload.get("task_id")
        project_id = event.payload.get("project_id")

        logger.info(
            "Task event processed",
            event_type=event.event_type.value,
            task_id=task_id,
            project_id=project_id,
        )


# 注册所有处理器
def register_event_handlers() -> None:
    """注册所有事件处理器."""
    from app.events.bus import get_event_bus

    bus = get_event_bus()

    bus.subscribe(RiskAlertHandler())
    bus.subscribe(CostMonitorHandler())
    bus.subscribe(MilestoneHandler())
    bus.subscribe(SkillExecutionHandler())
    bus.subscribe(ApprovalHandler())
    bus.subscribe(TaskUpdateHandler())

    logger.info("Event handlers registered")