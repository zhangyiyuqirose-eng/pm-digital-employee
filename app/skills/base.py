"""
PM Digital Employee - Base Skill
项目经理数字员工系统 - Skill基类定义

所有Skill必须继承BaseSkill，并提供Manifest定义。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.orchestrator.schemas import SkillManifest, SkillExecutionContext, SkillExecutionResult

logger = get_logger(__name__)


class BaseSkill(ABC):
    """
    Skill基类.

    所有Skill必须继承此基类并实现execute方法。
    """

    skill_name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "1.0.0"

    def __init__(
        self,
        manifest: Optional[SkillManifest] = None,
        context: Optional[SkillExecutionContext] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """初始化Skill."""
        self._manifest = manifest
        self._context = context
        self._session = session

    @property
    def user_id(self) -> Optional[str]:
        """获取用户ID."""
        return self._context.user_id if self._context else None

    @property
    def chat_id(self) -> Optional[str]:
        """获取聊天ID."""
        return self._context.chat_id if self._context else None

    @property
    def project_id(self) -> Optional[uuid.UUID]:
        """获取项目ID."""
        return self._context.project_id if self._context else None

    @property
    def params(self) -> Dict[str, Any]:
        """获取参数."""
        return self._context.params if self._context else {}

    def get_param(self, key: str, default: Any = None) -> Any:
        """获取单个参数."""
        return self.params.get(key, default)

    def build_success_result(
        self,
        output: Dict[str, Any],
        presentation_type: str = "text",
        presentation_data: Optional[Dict[str, Any]] = None,
    ) -> SkillExecutionResult:
        """构建成功结果."""
        return SkillExecutionResult(
            success=True,
            skill_name=self.skill_name,
            output=output,
            presentation_type=presentation_type,
            presentation_data=presentation_data,
        )

    def build_error_result(self, error_message: str) -> SkillExecutionResult:
        """构建错误结果."""
        return SkillExecutionResult(
            success=False,
            skill_name=self.skill_name,
            error_message=error_message,
        )

    @abstractmethod
    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        pass

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import SkillManifestBuilder

        builder = SkillManifestBuilder()
        builder.set_name(cls.skill_name, cls.display_name)
        builder.set_description(cls.description)
        builder.set_version(cls.version)
        return builder.build()

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        from app.orchestrator.skill_manifest import SkillManifestBuilder

        builder = SkillManifestBuilder()
        builder.set_name(cls.skill_name, cls.display_name)
        builder.set_description(cls.description)
        builder.set_version(cls.version)
        return builder.build()


class SkillRegistryMixin:
    """Skill注册混入类."""

    @classmethod
    def register(cls) -> None:
        """注册Skill到Registry."""
        from app.orchestrator.skill_registry import register_skill

        manifest = cls.get_manifest()
        register_skill(manifest, cls)


class SkillTestMixin:
    """Skill测试混入类."""

    @classmethod
    async def test_execute(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """测试执行Skill."""
        return {"success": True, "params": params}


def skill(
    skill_name: str,
    display_name: str,
    description: str,
    version: str = "1.0.0",
) -> type:
    """
    Skill装饰器.

    简化Skill定义。
    """
    def decorator(cls: type) -> type:
        cls.skill_name = skill_name
        cls.display_name = display_name
        cls.description = description
        cls.version = version
        return cls

    return decorator