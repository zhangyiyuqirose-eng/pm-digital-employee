"""
PM Digital Employee - Events Module
项目经理数字员工系统 - 事件总线模块

提供事件发布订阅模式，支持装饰器注册。
"""

from app.events.bus import (
    Event,
    EventBus,
    EventHandler,
    EventType,
    get_event_bus,
    subscribe,
    publish,
)
from app.events.handlers import (
    on_event,
    EventHandlerRegistry,
    RiskAlertHandler,
    CostMonitorHandler,
    MilestoneHandler,
    SkillExecutionHandler,
    ApprovalHandler,
    TaskUpdateHandler,
    register_event_handlers,
)

__all__ = [
    # Core
    "Event",
    "EventBus",
    "EventHandler",
    "EventType",
    "get_event_bus",
    "subscribe",
    "publish",
    # Decorator
    "on_event",
    "EventHandlerRegistry",
    # Handlers
    "RiskAlertHandler",
    "CostMonitorHandler",
    "MilestoneHandler",
    "SkillExecutionHandler",
    "ApprovalHandler",
    "TaskUpdateHandler",
    "register_event_handlers",
]