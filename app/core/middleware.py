"""
PM Digital Employee - Middleware
项目经理数字员工系统 - 请求中间件
"""

import time
import uuid
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger, set_trace_id

logger = get_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Trace ID中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成或获取Trace ID
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())

        # 设置到上下文
        set_trace_id(trace_id)

        # 调用下一个中间件
        response = await call_next(request)

        # 添加到响应头
        response.headers["X-Trace-ID"] = trace_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        # 调用下一个中间件
        response = await call_next(request)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        # 记录请求结束
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(
                "Unhandled exception",
                method=request.method,
                path=request.url.path,
                error=str(e),
            )

            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An internal error occurred",
                    },
                    "trace_id": request.headers.get("X-Trace-ID", ""),
                },
            )