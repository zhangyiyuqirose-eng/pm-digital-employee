"""
PM Digital Employee - Base Adapter
项目经理数字员工系统 - 第三方系统适配器基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAdapter(ABC):
    """
    第三方系统适配器基类.

    所有适配器必须继承此基类。
    """

    adapter_name: str = ""
    adapter_type: str = ""
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化适配器.

        Args:
            config: 配置信息
        """
        self._config = config or {}
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """
        连接系统.

        Returns:
            bool: 是否连接成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查.

        Returns:
            bool: 系统是否健康
        """
        pass

    @property
    def is_connected(self) -> bool:
        """是否已连接."""
        return self._is_connected

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值.

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        return self._config.get(key, default)


class ProjectSystemAdapter(BaseAdapter):
    """
    项目管理系统适配器基类.
    """

    adapter_type = "project_system"

    @abstractmethod
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目信息.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目信息
        """
        pass

    @abstractmethod
    async def list_projects(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        列出项目.

        Args:
            filters: 过滤条件

        Returns:
            List: 项目列表
        """
        pass

    @abstractmethod
    async def get_tasks(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """
        获取项目任务.

        Args:
            project_id: 项目ID

        Returns:
            List: 任务列表
        """
        pass

    @abstractmethod
    async def update_task(
        self,
        task_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        更新任务.

        Args:
            task_id: 任务ID
            data: 更新数据

        Returns:
            Dict: 更新结果
        """
        pass


class FinanceSystemAdapter(BaseAdapter):
    """
    财务系统适配器基类.
    """

    adapter_type = "finance_system"

    @abstractmethod
    async def get_budget(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        获取项目预算.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 预算信息
        """
        pass

    @abstractmethod
    async def get_actual_cost(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        获取实际支出.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 实际支出信息
        """
        pass


class DevOpsSystemAdapter(BaseAdapter):
    """
    DevOps系统适配器基类.
    """

    adapter_type = "devops_system"

    @abstractmethod
    async def get_build_status(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        获取构建状态.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 构建状态
        """
        pass

    @abstractmethod
    async def get_deployment_status(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        获取部署状态.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 部署状态
        """
        pass


class MockProjectSystemAdapter(ProjectSystemAdapter):
    """
    项目管理系统Mock适配器.

    用于开发和测试环境。
    """

    adapter_name = "mock_project_system"
    description = "项目管理系统Mock适配器"

    async def connect(self) -> bool:
        """连接."""
        self._is_connected = True
        return True

    async def disconnect(self) -> None:
        """断开连接."""
        self._is_connected = False

    async def health_check(self) -> bool:
        """健康检查."""
        return True

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """获取项目信息."""
        return {
            "project_id": project_id,
            "name": f"Mock项目_{project_id}",
            "status": "active",
            "progress": 65,
        }

    async def list_projects(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """列出项目."""
        return [
            {"project_id": "p1", "name": "Mock项目1", "status": "active"},
            {"project_id": "p2", "name": "Mock项目2", "status": "completed"},
        ]

    async def get_tasks(
        self,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """获取任务."""
        return [
            {"task_id": "t1", "name": "任务1", "status": "completed", "progress": 100},
            {"task_id": "t2", "name": "任务2", "status": "in_progress", "progress": 50},
        ]

    async def update_task(
        self,
        task_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """更新任务."""
        return {
            "task_id": task_id,
            "success": True,
            **data,
        }


# 适配器注册表
_ADAPTERS: Dict[str, type] = {
    "mock_project_system": MockProjectSystemAdapter,
}


def get_adapter(adapter_name: str, config: Optional[Dict] = None) -> BaseAdapter:
    """
    获取适配器实例.

    Args:
        adapter_name: 适配器名称
        config: 配置

    Returns:
        BaseAdapter: 适配器实例
    """
    adapter_class = _ADAPTERS.get(adapter_name)

    if adapter_class is None:
        raise ValueError(f"Unknown adapter: {adapter_name}")

    return adapter_class(config)


def register_adapter(name: str, adapter_class: type) -> None:
    """
    注册适配器.

    Args:
        name: 适配器名称
        adapter_class: 适配器类
    """
    _ADAPTERS[name] = adapter_class