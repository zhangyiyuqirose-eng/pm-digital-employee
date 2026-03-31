"""
PM Digital Employee - Skills Module
项目经理数字员工系统 - Skill插件模块初始化

实现Skill自动注册机制。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.orchestrator.skill_registry import SkillRegistry


def register_skills(registry: "SkillRegistry") -> None:
    """
    注册所有Skill到注册中心.

    此函数在应用启动时被调用，自动发现并注册所有Skill。

    Args:
        registry: Skill注册中心实例
    """
    # 一期MVP暂无具体Skill实现，后续阶段会添加
    # 示例：
    # from app.skills.project_overview_skill import ProjectOverviewSkill
    # registry.register(ProjectOverviewSkill())

    pass


__all__ = ["register_skills"]