"""
PM Digital Employee - Middleware
项目经理数字员工系统 - 请求中间件
"""

import asyncio
import time
import uuid
from collections import defaultdict
from typing import Any, Callable, Optional
from functools import wraps

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib

from app.core.config import settings
from app.core.logging import get_logger, set_trace_id
from app.core.exceptions import APIException, ErrorCode

logger = get_logger(__name__)


class RateLimiter:
    """API限流器"""

    def __init__(self):
        self.requests = defaultdict(list)  # 用户ID -> 请求时间列表
        self.max_requests = 10  # 每分钟最大请求数
        self.time_window = 60  # 时间窗口（秒）

    def is_allowed(self, user_id: str) -> bool:
        """检查用户是否允许请求"""
        now = time.time()
        # 清理过期的请求记录
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]

        # 检查是否超过限制
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # 记录当前请求
        self.requests[user_id].append(now)
        return True


class ConcurrentLimiter:
    """并发控制器"""

    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self):
        """获取许可"""
        await self.semaphore.acquire()

    def release(self):
        """释放许可"""
        self.semaphore.release()


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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件."""

    def __init__(self, app, max_requests: int = 10, time_window: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.rate_limiter.max_requests = max_requests
        self.rate_limiter.time_window = time_window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 尝试从请求头获取用户标识，或者使用IP地址
        user_id = request.headers.get("x-user-id") or request.client.host or "anonymous"

        # 检查是否允许请求
        if not self.rate_limiter.is_allowed(user_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "code": 429000,
                    "message": "请求频率超限，请稍后再试",
                    "details": {
                        "user_id": user_id,
                        "retry_after": self.rate_limiter.time_window
                    }
                }
            )

        response = await call_next(request)
        return response


class ConcurrentLimitMiddleware(BaseHTTPMiddleware):
    """并发控制中间件."""

    def __init__(self, app, max_concurrent: int = 20):
        super().__init__(app)
        self.concurrent_limiter = ConcurrentLimiter(max_concurrent)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取并发控制许可
        await self.concurrent_limiter.acquire()
        try:
            response = await call_next(request)
        finally:
            self.concurrent_limiter.release()
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 记录请求信息
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )

        # 调用下一个中间件
        response = await call_next(request)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        # 记录请求结束
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            }
        )

        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except APIException as e:
            # 已知API异常，使用标准格式返回
            return JSONResponse(
                status_code=200,  # 业务错误仍然返回200
                content=e.to_dict()
            )
        except HTTPException:
            # FastAPI HTTP异常，直接抛出
            raise
        except Exception as e:
            logger.exception(
                "Unhandled exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                }
            )

            # 创建跟踪ID用于错误追踪
            trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

            api_exc = APIException(
                error_code=ErrorCode.SYSTEM_ERROR,
                message="系统内部错误",
                details={"error_class": e.__class__.__name__, "error_args": str(e.args)},
                trace_id=trace_id
            )

            return JSONResponse(
                status_code=200,
                content=api_exc.to_dict()
            )


def rate_limit_decorator(user_identifier: str = "user_id"):
    """限流装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取用户标识
            if user_identifier in kwargs:
                user_id = kwargs[user_identifier]
            else:
                # 尝试从其他参数获取用户ID
                user_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

            # 检查限流
            rate_limiter = RateLimiter()
            if not rate_limiter.is_allowed(user_id):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "success": False,
                        "code": 429000,
                        "message": "请求频率超限，请稍后再试"
                    }
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def concurrent_control_decorator(func):
    """并发控制装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        concurrent_limiter = ConcurrentLimiter()
        await concurrent_limiter.acquire()
        try:
            return await func(*args, **kwargs)
        finally:
            concurrent_limiter.release()
    return wrapper