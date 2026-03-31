"""
PM Digital Employee - Logging
项目经理数字员工系统 - 结构化日志
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

# Trace ID上下文变量
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def set_trace_id(trace_id: str) -> None:
    """设置当前请求的Trace ID."""
    _trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """获取当前请求的Trace ID."""
    return _trace_id_var.get()


def add_trace_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """添加Trace ID到日志."""
    trace_id = get_trace_id()
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def get_logging_processors() -> list[Processor]:
    """获取日志处理器列表."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_trace_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]


def configure_logging() -> None:
    """配置结构化日志."""
    # 配置structlog
    structlog.configure(
        processors=get_logging_processors(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # 抑制第三方库日志
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    获取日志记录器.

    Args:
        name: 日志记录器名称

    Returns:
        structlog.stdlib.BoundLogger: 日志记录器
    """
    return structlog.get_logger(name)


# 配置日志
configure_logging()