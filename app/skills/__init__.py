"""
PM Digital Employee - Skills Module
项目经理数字员工系统 - Skill插件模块

包含13个核心Skill实现。
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
    from app.skills.project_overview_skill import ProjectOverviewSkill
    from app.skills.weekly_report_skill import WeeklyReportSkill
    from app.skills.policy_qa_skill import PolicyQASkill, TaskUpdateSkill, RiskAlertSkill, CostMonitorSkill
    from app.skills.additional_skills import WBSGenerationSkill, ProjectQuerySkill, MeetingMinutesSkill, ComplianceReviewSkill
    

    # Skill类映射
    skill_classes = {
        "project_overview": ProjectOverviewSkill,
        "weekly_report": WeeklyReportSkill,
        "policy_qa": PolicyQASkill,
        "task_update": TaskUpdateSkill,
        "risk_alert": RiskAlertSkill,
        "cost_monitor": CostMonitorSkill,
        "wbs_generation": WBSGenerationSkill,
        "project_query": ProjectQuerySkill,
        "meeting_minutes": MeetingMinutesSkill,
        "compliance_review": ComplianceReviewSkill,
    }

    for skill_name, manifest in DEFAULT_SKILL_MANIFESTS.items():
        skill_class = skill_classes.get(skill_name)
        register_skill(manifest, skill_class)


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