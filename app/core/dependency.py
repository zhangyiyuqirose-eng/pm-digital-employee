"""
PM Digital Employee - Dependency Injection Container
项目经理数字员工系统 - 依赖注入容器

提供统一的服务依赖管理，替代全局单例模式。
支持FastAPI依赖注入和测试mock。
"""

from functools import lru_cache
from typing import AsyncGenerator, Optional, TypeVar

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ServiceContainer:
    """
    服务容器.

    管理服务的创建和生命周期，替代全局单例。
    支持延迟初始化和依赖注入。
    """

    def __init__(self) -> None:
        """初始化容器."""
        self._services: dict = {}
        self._factories: dict = {}
        self._initialized = False

    def register_factory(
        self,
        service_type: type,
        factory: callable,
    ) -> None:
        """
        注册服务工厂.

        Args:
            service_type: 服务类型
            factory: 创建服务的工厂函数
        """
        self._factories[service_type] = factory

    def register_instance(
        self,
        service_type: type,
        instance: object,
    ) -> None:
        """
        注册服务实例.

        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        self._services[service_type] = instance

    def get(self, service_type: type[T]) -> T:
        """
        获取服务实例.

        Args:
            service_type: 服务类型

        Returns:
            服务实例
        """
        # 返回已存在的实例
        if service_type in self._services:
            return self._services[service_type]

        # 使用工厂创建
        if service_type in self._factories:
            instance = self._factories[service_type]()
            self._services[service_type] = instance
            return instance

        raise KeyError(f"Service {service_type.__name__} not registered")

    def has(self, service_type: type) -> bool:
        """检查服务是否注册."""
        return service_type in self._services or service_type in self._factories

    def clear(self) -> None:
        """清空容器（用于测试）."""
        self._services.clear()
        self._initialized = False


# 全局容器实例
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """获取服务容器实例."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _register_default_services(_container)
    return _container


def _register_default_services(container: ServiceContainer) -> None:
    """注册默认服务."""
    from app.ai.llm_gateway import LLMGateway
    from app.ai.output_parser import (
        StructuredOutputParser,
        IntentOutputParser,
        RiskOutputParser,
    )
    from app.integrations.lark.client import LarkClient
    from app.integrations.lark.service import LarkService
    from app.events.bus import EventBus

    # 注册Settings
    container.register_instance(Settings, get_settings())

    # 注册LLMGateway
    container.register_factory(LLMGateway, lambda: LLMGateway())

    # 注册OutputParser
    container.register_factory(
        StructuredOutputParser,
        lambda: StructuredOutputParser(),
    )
    container.register_factory(
        IntentOutputParser,
        lambda: IntentOutputParser(),
    )
    container.register_factory(
        RiskOutputParser,
        lambda: RiskOutputParser(),
    )

    # 注册LarkClient和Service
    container.register_factory(LarkClient, lambda: LarkClient())
    container.register_factory(LarkService, lambda: LarkService())

    # 注册EventBus
    container.register_factory(EventBus, lambda: EventBus())


# ============================================
# FastAPI依赖注入函数
# ============================================

@lru_cache()
def get_settings_dep() -> Settings:
    """FastAPI依赖: Settings."""
    return get_settings()


def get_llm_gateway_dep() -> "LLMGateway":
    """FastAPI依赖: LLMGateway."""
    from app.ai.llm_gateway import LLMGateway
    return get_container().get(LLMGateway)


def get_lark_client_dep() -> "LarkClient":
    """FastAPI依赖: LarkClient."""
    from app.integrations.lark.client import LarkClient
    return get_container().get(LarkClient)


def get_lark_service_dep() -> "LarkService":
    """FastAPI依赖: LarkService."""
    from app.integrations.lark.service import LarkService
    return get_container().get(LarkService)


def get_event_bus_dep() -> "EventBus":
    """FastAPI依赖: EventBus."""
    from app.events.bus import EventBus
    return get_container().get(EventBus)


async def get_db_session_dep() -> AsyncGenerator:
    """FastAPI依赖: Database Session."""
    from app.db.session import get_async_session
    async for session in get_async_session():
        yield session


def get_redis_dep() -> "Redis":
    """FastAPI依赖: Redis."""
    from app.db.session import get_redis_client
    return get_redis_client()


# ============================================
# 服务获取函数（兼容旧代码）
# ============================================

def get_service(service_type: type[T]) -> T:
    """
    获取服务实例（通用函数）.

    Args:
        service_type: 服务类型

    Returns:
        服务实例
    """
    return get_container().get(service_type)


def reset_container() -> None:
    """
    重置容器（用于测试）.

    清空所有服务，重新初始化。
    """
    global _container
    if _container:
        _container.clear()
    _container = None


# ============================================
# 测试辅助函数
# ============================================

def mock_service(service_type: type, mock_instance: object) -> None:
    """
    Mock服务（用于测试）.

    Args:
        service_type: 服务类型
        mock_instance: Mock实例
    """
    container = get_container()
    container.register_instance(service_type, mock_instance)


def use_test_container() -> ServiceContainer:
    """
    创建测试容器.

    返回一个独立的容器用于测试，
    不会影响全局容器。
    """
    test_container = ServiceContainer()
    _register_default_services(test_container)
    return test_container


__all__ = [
    "ServiceContainer",
    "get_container",
    "get_service",
    "reset_container",
    "mock_service",
    "use_test_container",
    # FastAPI依赖
    "get_settings_dep",
    "get_llm_gateway_dep",
    "get_lark_client_dep",
    "get_lark_service_dep",
    "get_event_bus_dep",
    "get_db_session_dep",
    "get_redis_dep",
]