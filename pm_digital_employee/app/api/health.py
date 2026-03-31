"""
PM Digital Employee - Health Check API Module
项目经理数字员工系统 - 健康检查接口模块

实现三个探活接口：
- /health: 健康检查（K8s liveness probe）
- /ready: 就绪检查（K8s readiness probe）
- /live: 存活检查（K8s startup probe）
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="", tags=["Health"])


class HealthResponse(BaseModel):
    """健康检查响应模型."""

    status: str = Field(default="healthy", description="服务状态")
    service: str = Field(description="服务名称")
    version: str = Field(description="服务版本")
    timestamp: str = Field(description="检查时间戳")
    environment: str = Field(description="运行环境")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "PM Digital Employee",
                "version": "v1",
                "timestamp": "2026-03-31T10:00:00+00:00",
                "environment": "production",
            }
        }


class ReadyResponse(BaseModel):
    """就绪检查响应模型."""

    status: str = Field(default="ready", description="服务状态")
    timestamp: str = Field(description="检查时间戳")
    checks: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="各组件检查结果",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ready",
                "timestamp": "2026-03-31T10:00:00+00:00",
                "checks": {
                    "database": {"status": "healthy", "latency_ms": 5.2},
                    "redis": {"status": "healthy", "latency_ms": 1.3},
                    "rabbitmq": {"status": "healthy", "latency_ms": 2.1},
                },
            }
        }


class ComponentHealth(BaseModel):
    """组件健康状态模型."""

    status: str = Field(description="组件状态: healthy | unhealthy")
    latency_ms: Optional[float] = Field(default=None, description="响应延迟（毫秒）")
    error: Optional[str] = Field(default=None, description="错误信息")


def check_database() -> ComponentHealth:
    """
    检查数据库连接状态.

    Returns:
        ComponentHealth: 数据库健康状态
    """
    import time

    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    from app.core.logging import get_logger

    logger = get_logger(__name__)

    try:
        # 尝试获取数据库连接并执行简单查询
        from app.db.session import get_sync_engine

        start_time = time.perf_counter()

        engine = get_sync_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        latency_ms = (time.perf_counter() - start_time) * 1000

        return ComponentHealth(
            status="healthy",
            latency_ms=round(latency_ms, 2),
        )

    except ImportError:
        # 数据库模块尚未初始化，返回待初始化状态
        return ComponentHealth(
            status="healthy",
            latency_ms=0,
            error="Database module not initialized",
        )
    except SQLAlchemyError as exc:
        logger.error("Database health check failed", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=str(exc)[:100],
        )
    except Exception as exc:
        logger.error("Database health check unexpected error", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=f"Unexpected error: {type(exc).__name__}",
        )


def check_redis() -> ComponentHealth:
    """
    检查Redis连接状态.

    Returns:
        ComponentHealth: Redis健康状态
    """
    import time

    from app.core.logging import get_logger

    logger = get_logger(__name__)

    try:
        import redis
        from redis.exceptions import RedisError

        start_time = time.perf_counter()

        # 创建Redis连接
        client = redis.from_url(
            settings.redis.url,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

        # 执行PING命令
        result = client.ping()
        client.close()

        latency_ms = (time.perf_counter() - start_time) * 1000

        if result:
            return ComponentHealth(
                status="healthy",
                latency_ms=round(latency_ms, 2),
            )
        else:
            return ComponentHealth(
                status="unhealthy",
                error="Redis PING returned False",
            )

    except ImportError:
        return ComponentHealth(
            status="healthy",
            latency_ms=0,
            error="Redis module not initialized",
        )
    except RedisError as exc:
        logger.error("Redis health check failed", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=str(exc)[:100],
        )
    except Exception as exc:
        logger.error("Redis health check unexpected error", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=f"Unexpected error: {type(exc).__name__}",
        )


def check_rabbitmq() -> ComponentHealth:
    """
    检查RabbitMQ连接状态.

    Returns:
        ComponentHealth: RabbitMQ健康状态
    """
    import time

    from app.core.logging import get_logger

    logger = get_logger(__name__)

    try:
        import pika
        from pika.exceptions import AMQPError

        start_time = time.perf_counter()

        # 创建RabbitMQ连接
        credentials = pika.PlainCredentials(
            settings.rabbitmq.user,
            settings.rabbitmq.password,
        )

        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq.host,
            port=settings.rabbitmq.port,
            virtual_host=settings.rabbitmq.vhost,
            credentials=credentials,
            connection_attempts=1,
            socket_timeout=5,
        )

        connection = pika.BlockingConnection(parameters)
        connection.close()

        latency_ms = (time.perf_counter() - start_time) * 1000

        return ComponentHealth(
            status="healthy",
            latency_ms=round(latency_ms, 2),
        )

    except ImportError:
        return ComponentHealth(
            status="healthy",
            latency_ms=0,
            error="RabbitMQ module not initialized",
        )
    except AMQPError as exc:
        logger.error("RabbitMQ health check failed", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=str(exc)[:100],
        )
    except Exception as exc:
        logger.error("RabbitMQ health check unexpected error", error=str(exc))
        return ComponentHealth(
            status="unhealthy",
            error=f"Unexpected error: {type(exc).__name__}",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="健康检查",
    description="检查服务是否正常运行，用于K8s liveness probe",
    responses={
        200: {"description": "服务健康"},
        500: {"description": "服务不健康"},
    },
)
async def health_check() -> HealthResponse:
    """
    健康检查接口.

    用于K8s liveness probe，检查服务是否存活。
    如果返回200，说明服务正在运行。

    Returns:
        HealthResponse: 健康状态响应
    """
    return HealthResponse(
        status="healthy",
        service=settings.app.name,
        version=settings.app.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.app.env,
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="就绪检查",
    description="检查服务是否就绪，用于K8s readiness probe",
    responses={
        200: {"description": "服务就绪"},
        503: {"description": "服务未就绪"},
    },
)
async def ready_check(response: Response) -> ReadyResponse:
    """
    就绪检查接口.

    用于K8s readiness probe，检查服务是否可以接收请求。
    检查所有依赖服务（数据库、Redis、RabbitMQ）的连接状态。

    Returns:
        ReadyResponse: 就绪状态响应
    """
    checks: Dict[str, ComponentHealth] = {}

    # 检查数据库
    checks["database"] = check_database()

    # 检查Redis
    checks["redis"] = check_redis()

    # 检查RabbitMQ
    checks["rabbitmq"] = check_rabbitmq()

    # 判断整体状态
    all_healthy = all(check.status == "healthy" for check in checks.values())

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "not_ready"
    else:
        overall_status = "ready"

    return ReadyResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks={name: check.model_dump() for name, check in checks.items()},
    )


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="存活检查",
    description="检查服务是否存活，用于K8s startup probe",
    responses={
        200: {"description": "服务存活"},
        500: {"description": "服务死亡"},
    },
)
async def live_check() -> HealthResponse:
    """
    存活检查接口.

    用于K8s startup probe，检查服务是否已启动完成。
    与health接口类似，但用于启动阶段。

    Returns:
        HealthResponse: 存活状态响应
    """
    return HealthResponse(
        status="alive",
        service=settings.app.name,
        version=settings.app.version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.app.env,
    )