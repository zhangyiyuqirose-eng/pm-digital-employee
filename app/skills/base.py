"""
PM Digital Employee - Base Skill
项目经理数字员工系统 - Skill基类定义

所有Skill必须继承BaseSkill，并提供Manifest定义。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.orchestrator.schemas import SkillManifest

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