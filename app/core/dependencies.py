"""
PM Digital Employee - Dependency Injection
项目经理数字员工系统 - 依赖注入框架

提供FastAPI依赖注入支持，替代全局单例模式。

使用方式:
```python
from fastapi import Depends
from app.core.dependencies import get_lark_service_dep, get_llm_gateway_dep

@router.post("/webhook")
async def handle_webhook(
    service: LarkService = Depends(get_lark_service_dep),
):
    ...
```
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ==================== Session Dependencies ====================


async def get_db_session() -> AsyncGenerator:
    """
    获取数据库会话（依赖注入版本）.

    Yields:
        AsyncSession: 数据库会话
    """
    from app.db.session import DatabaseManager, get_async_session_factory

    session_factory = get_async_session_factory()
    if session_factory is None:
        raise RuntimeError("Database session factory not initialized")

    async with session_factory() as session:
        yield session


# ==================== Service Dependencies ====================


def get_lark_service_dep():
    """
    获取飞书服务（依赖注入版本）.

    Returns:
        LarkService: 飞书服务实例

    Note:
        当前返回全局实例，后续可替换为请求级实例
    """
    from app.integrations.lark.service import get_lark_service

    return get_lark_service()


def get_llm_gateway_dep():
    """
    获取LLM网关（依赖注入版本）.

    Returns:
        LLMGateway: LLM网关实例
    """
    from app.ai.llm_gateway import get_llm_gateway

    return get_llm_gateway()


def get_intent_router_dep():
    """
    获取意图路由器（依赖注入版本）.

    Returns:
        IntentRouterV2: 意图路由器实例
    """
    from app.orchestrator.intent_router import get_intent_router_v2

    return get_intent_router_v2()


def get_skill_registry_dep():
    """
    获取Skill注册表（依赖注入版本）.

    Returns:
        SkillRegistry: Skill注册表实例
    """
    from app.orchestrator.skill_registry import get_skill_registry

    return get_skill_registry()


def get_orchestrator_dep():
    """
    获取编排器（依赖注入版本）.

    Returns:
        Orchestrator: 编排器实例
    """
    from app.orchestrator.orchestrator import get_orchestrator

    return get_orchestrator()


def get_context_service_dep():
    """
    获取上下文服务（依赖注入版本）.

    Returns:
        ContextService: 上下文服务实例
    """
    from app.services.context_service import get_context_service

    return get_context_service()


def get_dialog_state_machine_dep():
    """
    获取对话状态机（依赖注入版本）.

    Returns:
        DialogStateMachine: 对话状态机实例
    """
    from app.orchestrator.dialog_state import get_dialog_state_machine

    return get_dialog_state_machine()


def get_idempotency_service_dep():
    """
    获取幂等服务（依赖注入版本）.

    Returns:
        MessageIdempotencyService: 消息幂等服务实例
    """
    from app.services.idempotency_service import get_message_idempotency_service

    return get_message_idempotency_service()


def get_encryptor_dep():
    """
    获取加密器（依赖注入版本）.

    Returns:
        DataEncryptor: 数据加密器实例
    """
    from app.core.encryption import get_encryptor

    return get_encryptor()


# ==================== Repository Dependencies ====================


def get_user_repository_dep(session=Depends(get_db_session)):
    """
    获取用户Repository（依赖注入版本）.

    Args:
        session: 数据库会话（由依赖注入提供）

    Returns:
        UserRepository: 用户Repository实例
    """
    from app.repositories.user_repository import UserRepository

    return UserRepository(session)


def get_project_repository_dep(session=Depends(get_db_session)):
    """
    获取项目Repository（依赖注入版本）.

    Returns:
        ProjectRepository: 项目Repository实例
    """
    from app.repositories.project_repository import ProjectRepository

    return ProjectRepository(session)


def get_task_repository_dep(session=Depends(get_db_session)):
    """
    获取任务Repository（依赖注入版本）.

    Returns:
        TaskRepository: 任务Repository实例
    """
    from app.repositories.task_repository import TaskRepository

    return TaskRepository(session)


# ==================== Unit of Work Dependencies ====================


async def get_unit_of_work_dep(session=Depends(get_db_session)) -> AsyncGenerator:
    """
    获取工作单元（依赖注入版本）.

    Yields:
        UnitOfWork: 工作单元实例

    Example:
        ```python
        @router.post("/projects")
        async def create_project(
            uow: UnitOfWork = Depends(get_unit_of_work_dep),
        ):
            async with uow.transaction():
                ...
        ```
    """
    from app.core.unit_of_work import UnitOfWork

    uow = UnitOfWork(session)
    yield uow


# ==================== Dependency Container ====================


class DependencyContainer:
    """
    依赖容器.

    用于管理依赖的生命周期和缓存。
    支持单例和请求级依赖。

    使用方式:
        ```python
        container = DependencyContainer()

        # 注册依赖
        container.register("lark_service", get_lark_service_dep)

        # 获取依赖
        service = container.get("lark_service")
        ```
    """

    def __init__(self) -> None:
        """初始化容器."""
        self._dependencies: dict = {}
        self._instances: dict = {}

    def register(self, name: str, factory: callable) -> None:
        """
        注册依赖工厂.

        Args:
            name: 依赖名称
            factory: 工厂函数
        """
        self._dependencies[name] = factory

    def get(self, name: str) -> any:
        """
        获取依赖实例.

        Args:
            name: 依赖名称

        Returns:
            依赖实例
        """
        if name not in self._dependencies:
            raise KeyError(f"Dependency '{name}' not registered")

        # 缓存单例实例
        if name not in self._instances:
            self._instances[name] = self._dependencies[name]()

        return self._instances[name]

    def clear(self) -> None:
        """清除所有缓存的实例."""
        self._instances.clear()


# 全局容器实例
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """
    获取依赖容器实例.

    Returns:
        DependencyContainer: 依赖容器
    """
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container