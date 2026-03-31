"""
PM Digital Employee - Skills Module
项目经理数字员工系统 - Skill插件模块

包含10个核心Skill实现。
"""

from app.orchestrator.skill_manifest import (
    DEFAULT_SKILL_MANIFESTS,
    get_project_overview_manifest,
    get_weekly_report_manifest,
    get_wbs_generation_manifest,
    get_task_update_manifest,
    get_risk_alert_manifest,
    get_cost_monitor_manifest,
    get_policy_qa_manifest,
    get_project_query_manifest,
    get_meeting_minutes_manifest,
    get_compliance_review_manifest,
)


def register_all_skills() -> None:
    """注册所有Skill到Registry."""
    from app.orchestrator.skill_registry import register_skill

    for skill_name, manifest in DEFAULT_SKILL_MANIFESTS.items():
        register_skill(manifest)


__all__ = [
    "DEFAULT_SKILL_MANIFESTS",
    "get_project_overview_manifest",
    "get_weekly_report_manifest",
    "get_wbs_generation_manifest",
    "get_task_update_manifest",
    "get_risk_alert_manifest",
    "get_cost_monitor_manifest",
    "get_policy_qa_manifest",
    "get_project_query_manifest",
    "get_meeting_minutes_manifest",
    "get_compliance_review_manifest",
    "register_all_skills",
]