"""
PM Digital Employee - Skill Registry
项目经理数字员工系统 - Skill注册中心

管理所有Skill的注册、发现、配置。
"""

from typing import Any, Dict, List, Optional, Set

from app.core.logging import get_logger
from app.orchestrator.schemas import SkillManifest

logger = get_logger(__name__)


class SkillRegistry:
    """
    Skill注册中心.

    管理所有Skill的注册、发现、配置。
    """

    def __init__(self) -> None:
        """初始化Skill注册中心."""
        self._skills: Dict[str, SkillManifest] = {}
        self._skill_classes: Dict[str, Any] = {}

        logger.info("Skill registry initialized")

    def register(
        self,
        manifest: SkillManifest,
        skill_class: Optional[Any] = None,
    ) -> None:
        """
        注册Skill.

        Args:
            manifest: Skill Manifest
            skill_class: Skill实现类
        """
        skill_name = manifest.skill_name

        if skill_name in self._skills:
            logger.warning(
                "Skill already registered, updating",
                skill_name=skill_name,
            )

        self._skills[skill_name] = manifest

        if skill_class:
            self._skill_classes[skill_name] = skill_class

        logger.info(
            "Skill registered",
            skill_name=skill_name,
            version=manifest.version,
        )

    def unregister(self, skill_name: str) -> bool:
        """
        注销Skill.

        Args:
            skill_name: Skill名称

        Returns:
            bool: 是否成功注销
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            if skill_name in self._skill_classes:
                del self._skill_classes[skill_name]
            logger.info("Skill unregistered", skill_name=skill_name)
            return True
        return False

    def get_manifest(self, skill_name: str) -> SkillManifest:
        """
        获取Skill Manifest.

        Args:
            skill_name: Skill名称

        Returns:
            SkillManifest: Manifest对象

        Raises:
            KeyError: Skill不存在
        """
        manifest = self._skills.get(skill_name)
        if manifest is None:
            raise KeyError(f"Skill not found: {skill_name}")
        return manifest

    def get_skill_class(self, skill_name: str) -> Optional[Any]:
        """
        获取Skill实现类.

        Args:
            skill_name: Skill名称

        Returns:
            Optional[Any]: Skill类
        """
        return self._skill_classes.get(skill_name)

    def list_all_skills(self) -> List[SkillManifest]:
        """
        列出所有注册的Skill.

        Returns:
            List[SkillManifest]: Skill列表
        """
        return list(self._skills.values())

    def get_skill_descriptions(self) -> Dict[str, str]:
        """
        获取所有Skill描述（用于意图识别）.

        Returns:
            Dict[str, str]: Skill名称到描述的映射
        """
        return {
            name: manifest.description
            for name, manifest in self._skills.items()
        }

    def get_skill_display_names(self) -> Dict[str, str]:
        """
        获取所有Skill显示名称.

        Returns:
            Dict[str, str]: Skill名称到显示名称的映射
        """
        return {
            name: manifest.display_name
            for name, manifest in self._skills.items()
        }

    def get_skill_names(self) -> Set[str]:
        """
        获取所有Skill名称集合.

        Returns:
            Set[str]: Skill名称集合
        """
        return set(self._skills.keys())


# 全局Skill注册中心实例
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """
    获取全局Skill注册中心实例.

    Returns:
        SkillRegistry: 注册中心实例
    """
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry


def register_skill(
    manifest: SkillManifest,
    skill_class: Optional[Any] = None,
) -> None:
    """
    便捷函数：注册Skill.

    Args:
        manifest: Skill Manifest
        skill_class: Skill实现类
    """
    registry = get_skill_registry()
    registry.register(manifest, skill_class)


def get_skill_manifest(skill_name: str) -> SkillManifest:
    """
    便捷函数：获取Skill Manifest.

    Args:
        skill_name: Skill名称

    Returns:
        SkillManifest: Manifest对象
    """
    registry = get_skill_registry()
    return registry.get_manifest(skill_name)