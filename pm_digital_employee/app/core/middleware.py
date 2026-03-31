"""
PM Digital Employee - Request Middleware Module
项目经理数字员工系统 - 请求中间件模块

实现全局请求处理能力：
- trace_id全链路透传
- 请求日志记录
- 统一异常处理
- 请求计时
- 审计日志占位
"""

import time
import uuid
from typing import Any, Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.exceptions import PMError, SystemError, ValidationError
from app.core.logging import (
    clear_context,
    get_logger,
    get_trace_id,
    set_project_id,
    set_trace_id,
    set_user_id,
)

logger = get_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Trace ID中间件.

    为每个请求生成或继承唯一的trace_id，
    用于全链路追踪和日志关联。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，注入trace_id.

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象
        """
        # 从请求头获取或生成trace_id
        trace_id = request.headers.get("X-Trace-ID") or request.headers.get("X-Request-ID")
        if not trace_id:
            trace_id = str(uuid.uuid4())

        # 设置到上下文变量
        set_trace_id(trace_id)

        try:
            response = await call_next(request)

            # 将trace_id添加到响应头
            response.headers["X-Trace-ID"] = trace_id

            return response
        finally:
            # 清除上下文（在请求结束时）
            clear_context()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件.

    记录每个请求的基本信息、耗时、状态码等。
    """

    # 不记录日志的路径
    EXCLUDED_PATHS = {
        "/health",
        "/ready",
        "/live",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，记录日志.

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象
        """
        # 检查是否跳过日志
        path = request.url.path
        should_skip = path in self.EXCLUDED_PATHS or path.startswith("/static/")

        if should_skip:
            return await call_next(request)

        # 记录请求开始时间
        start_time = time.perf_counter()

        # 获取客户端IP
        client_ip = self._get_client_ip(request)

        # 获取用户信息（如果有）
        user_id = request.headers.get("X-User-ID", "")
        if user_id:
            set_user_id(user_id)

        # 记录请求信息
        logger.info(
            "Request started",
            method=request.method,
            path=path,
            query=str(request.query_params),
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
        )

        try:
            response = await call_next(request)

            # 计算请求耗时
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 记录响应信息
            logger.info(
                "Request completed",
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
            )

            return response

        except Exception as exc:
            # 计算请求耗时
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 记录异常信息
            logger.error(
                "Request failed with exception",
                method=request.method,
                path=path,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
                error=str(exc),
                error_type=type(exc).__name__,
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址.

        支持代理场景，从X-Forwarded-For等头部获取。

        Args:
            request: 请求对象

        Returns:
            str: 客户端IP地址
        """
        # 优先从X-Forwarded-For获取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()

        # 从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 使用直连IP
        if request.client:
            return request.client.host

        return "unknown"


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    统一异常处理中间件.

    捕获所有未处理的异常，转换为统一格式的响应。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，捕获异常.

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象
        """
        try:
            return await call_next(request)
        except PMError as exc:
            # 业务异常，返回友好错误信息
            logger.warning(
                "Business exception occurred",
                error_code=exc.error_code.code,
                error_message=exc.message,
                trace_id=exc.trace_id or get_trace_id(),
                details=exc.details,
            )

            return JSONResponse(
                status_code=self._get_http_status(exc.error_code.code),
                content=exc.to_dict(),
                headers={"X-Trace-ID": exc.trace_id or get_trace_id()},
            )
        except RequestValidationError as exc:
            # 请求参数校验异常
            errors = []
            for error in exc.errors():
                errors.append(
                    {
                        "field": ".".join(str(loc) for loc in error["loc"]),
                        "message": error["msg"],
                        "type": error["type"],
                    }
                )

            validation_error = ValidationError(
                message="请求参数校验失败",
                trace_id=get_trace_id(),
                details={"errors": errors},
            )

            logger.warning(
                "Validation error",
                errors=errors,
                trace_id=get_trace_id(),
            )

            return JSONResponse(
                status_code=422,
                content=validation_error.to_dict(),
                headers={"X-Trace-ID": get_trace_id()},
            )
        except Exception as exc:
            # 未处理的异常，返回通用错误
            trace_id = get_trace_id()

            logger.exception(
                "Unhandled exception occurred",
                error=str(exc),
                error_type=type(exc).__name__,
                trace_id=trace_id,
            )

            # 生产环境不暴露详细错误信息
            if settings.is_production:
                system_error = SystemError(
                    trace_id=trace_id,
                    cause=exc,
                )
            else:
                system_error = SystemError(
                    message=f"Internal error: {exc}",
                    trace_id=trace_id,
                    details={"error_type": type(exc).__name__},
                    cause=exc,
                )

            return JSONResponse(
                status_code=500,
                content=system_error.to_dict(),
                headers={"X-Trace-ID": trace_id},
            )

    def _get_http_status(self, error_code: str) -> int:
        """
        根据错误码获取HTTP状态码.

        Args:
            error_code: 错误码字符串

        Returns:
            int: HTTP状态码
        """
        # 根据错误码前缀映射HTTP状态码
        if error_code.startswith("E2"):
            # 权限/认证错误
            if error_code in ("E2001", "E2003"):
                return 401
            return 403
        elif error_code.startswith("E4"):
            # 数据错误
            if error_code == "E4001":
                return 404
            return 400
        elif error_code.startswith("E3"):
            # 业务逻辑错误
            return 400
        elif error_code.startswith("E6"):
            # 安全错误
            return 400
        elif error_code.startswith("E1"):
            # 系统错误
            return 500
        else:
            return 500


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件.

    记录关键操作的审计日志（占位实现，后续对接审计服务）。
    """

    # 需要审计的路径前缀
    AUDITED_PATH_PREFIXES = [
        "/api/v1/",
        "/lark/",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求，记录审计日志.

        Args:
            request: 请求对象
            call_next: 下一个处理器

        Returns:
            Response: 响应对象
        """
        # 检查是否需要审计
        path = request.url.path
        should_audit = any(path.startswith(prefix) for prefix in self.AUDITED_PATH_PREFIXES)

        if not should_audit:
            return await call_next(request)

        # 记录请求开始时间
        start_time = time.perf_counter()

        # 构建审计日志数据
        audit_data = {
            "trace_id": get_trace_id(),
            "method": request.method,
            "path": path,
            "query": str(request.query_params),
            "client_ip": request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or (request.client.host if request.client else "unknown"),
            "user_agent": request.headers.get("User-Agent", ""),
            "user_id": request.headers.get("X-User-ID", ""),
        }

        try:
            response = await call_next(request)

            # 记录响应信息
            audit_data.update(
                {
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "result": "success" if response.status_code < 400 else "failed",
                }
            )

            # 写入审计日志（占位，后续对接审计服务）
            logger.info("Audit log", **audit_data)

            return response

        except Exception as exc:
            # 记录异常信息
            audit_data.update(
                {
                    "status_code": 500,
                    "duration_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "result": "error",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                }
            )

            # 写入审计日志
            logger.error("Audit log - exception", **audit_data)

            raise


def setup_middlewares(app: FastAPI) -> None:
    """
    配置应用中间件.

    中间件执行顺序（从外到内）：
    1. TraceIDMiddleware - trace_id注入
    2. RequestLoggingMiddleware - 请求日志
    3. AuditMiddleware - 审计日志
    4. ExceptionHandlerMiddleware - 异常处理

    Args:
        app: FastAPI应用实例
    """
    # 注意：中间件的添加顺序与执行顺序相反
    # 最后添加的最先执行

    # 异常处理中间件（最内层）
    app.add_middleware(ExceptionHandlerMiddleware)

    # 审计日志中间件
    if settings.audit.enable:
        app.add_middleware(AuditMiddleware)

    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # Trace ID中间件（最外层）
    app.add_middleware(TraceIDMiddleware)

    logger.info(
        "Middlewares configured",
        middlewares=[
            "TraceIDMiddleware",
            "RequestLoggingMiddleware",
            "AuditMiddleware" if settings.audit.enable else None,
            "ExceptionHandlerMiddleware",
        ],
    )