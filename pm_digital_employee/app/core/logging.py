"""
PM Digital Employee - Structured Logging Module
项目经理数字员工系统 - 结构化日志配置模块

使用structlog实现结构化JSON日志，支持：
- 结构化JSON输出
- 日志分级
- trace_id全链路透传
- 上下文绑定
- 文件轮转
- 性能优化
"""

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder
from structlog.types import EventDict, Processor

from app.core.config import settings


# ContextVar用于存储trace_id，确保异步环境下正确传递
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
project_id_var: ContextVar[str] = ContextVar("project_id", default="")


def add_trace_id(logger: structlog.typing.BindableLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    添加trace_id到日志事件.

    Args:
        logger: structlog logger实例
        method_name: 日志方法名
        event_dict: 日志事件字典

    Returns:
        EventDict: 包含trace_id的日志事件字典
    """
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id

    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id

    project_id = project_id_var.get()
    if project_id:
        event_dict["project_id"] = project_id

    return event_dict


def add_app_info(logger: structlog.typing.BindableLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    添加应用信息到日志事件.

    Args:
        logger: structlog logger实例
        method_name: 日志方法名
        event_dict: 日志事件字典

    Returns:
        EventDict: 包含应用信息的日志事件字典
    """
    event_dict["app_name"] = settings.app.name
    event_dict["app_env"] = settings.app.env
    return event_dict


def drop_color_message_key(logger: structlog.typing.BindableLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    移除颜色消息键（用于JSON输出）.

    Args:
        logger: structlog logger实例
        method_name: 日志方法名
        event_dict: 日志事件字典

    Returns:
        EventDict: 移除颜色键后的日志事件字典
    """
    event_dict.pop("color_message", None)
    return event_dict


def timestamp_formatter(logger: structlog.typing.BindableLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    格式化时间戳为ISO 8601格式.

    Args:
        logger: structlog logger实例
        method_name: 日志方法名
        event_dict: 日志事件字典

    Returns:
        EventDict: 包含格式化时间戳的日志事件字典
    """
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def severity_mapper(logger: structlog.typing.BindableLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    将日志级别映射到severity字段（兼容云日志平台）.

    Args:
        logger: structlog logger实例
        method_name: 日志方法名
        event_dict: 日志事件字典

    Returns:
        EventDict: 包含severity字段的日志事件字典
    """
    # 日志级别映射表
    level_to_severity = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
        "exception": "ERROR",
    }

    level = event_dict.get("level", method_name)
    event_dict["severity"] = level_to_severity.get(level, "INFO")
    return event_dict


def get_shared_processors() -> list[Processor]:
    """
    获取共享的日志处理器列表.

    Returns:
        list[Processor]: 共享处理器列表
    """
    return [
        # 添加调用位置信息
        structlog.contextvars.merge_contextvars,
        add_trace_id,
        add_app_info,
        CallsiteParameterAdder(
            [
                CallsiteParameter.FILENAME,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
        structlog.stdlib.ExtraAdder,
        timestamp_formatter,
        severity_mapper,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def setup_logging() -> None:
    """
    配置结构化日志系统.

    根据配置初始化structlog和标准logging，
    支持JSON格式和文本格式输出。
    """
    # 获取日志级别
    log_level = getattr(logging, settings.log.level.upper(), logging.INFO)

    # 配置标准logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # 配置structlog处理器
    if settings.log.format == "json":
        # JSON格式（生产环境推荐）
        processors: list[Processor] = get_shared_processors() + [
            drop_color_message_key,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # 文本格式（开发环境）
        processors = get_shared_processors() + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # 配置structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    获取logger实例.

    Args:
        name: logger名称，默认为调用模块名

    Returns:
        structlog.stdlib.BoundLogger: logger实例
    """
    return structlog.get_logger(name)


def set_trace_id(trace_id: str) -> None:
    """
    设置当前请求的trace_id.

    Args:
        trace_id: 唯一追踪标识
    """
    trace_id_var.set(trace_id)


def get_trace_id() -> str:
    """
    获取当前请求的trace_id.

    Returns:
        str: trace_id值
    """
    return trace_id_var.get()


def set_user_id(user_id: str) -> None:
    """
    设置当前请求的用户ID.

    Args:
        user_id: 飞书用户ID
    """
    user_id_var.set(user_id)


def set_project_id(project_id: str) -> None:
    """
    设置当前请求的项目ID.

    Args:
        project_id: 项目ID
    """
    project_id_var.set(project_id)


def clear_context() -> None:
    """
    清除日志上下文变量.
    """
    trace_id_var.set("")
    user_id_var.set("")
    project_id_var.set("")


# 初始化日志系统
setup_logging()

# 默认logger实例
logger = get_logger(__name__)


class LogContext:
    """
    日志上下文管理器.

    用于在代码块中自动设置和清除日志上下文，
    支持with语句使用。

    Example:
        with LogContext(trace_id="abc123", user_id="ou_xxx", project_id="P001"):
            logger.info("Processing request")
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        **extra: Any,
    ) -> None:
        """
        初始化日志上下文.

        Args:
            trace_id: 追踪ID
            user_id: 用户ID
            project_id: 项目ID
            extra: 其他上下文信息
        """
        self._trace_id = trace_id or ""
        self._user_id = user_id or ""
        self._project_id = project_id or ""
        self._extra = extra
        self._old_trace_id: Optional[str] = None
        self._old_user_id: Optional[str] = None
        self._old_project_id: Optional[str] = None

    def __enter__(self) -> "LogContext":
        """
        进入上下文，保存旧值并设置新值.

        Returns:
            LogContext: 上下文实例
        """
        self._old_trace_id = trace_id_var.get()
        self._old_user_id = user_id_var.get()
        self._old_project_id = project_id_var.get()

        if self._trace_id:
            set_trace_id(self._trace_id)
        if self._user_id:
            set_user_id(self._user_id)
        if self._project_id:
            set_project_id(self._project_id)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        退出上下文，恢复旧值.
        """
        if self._old_trace_id is not None:
            trace_id_var.set(self._old_trace_id)
        if self._old_user_id is not None:
            user_id_var.set(self._old_user_id)
        if self._old_project_id is not None:
            project_id_var.set(self._old_project_id)