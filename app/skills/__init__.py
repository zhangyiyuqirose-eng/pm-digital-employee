"""
PM Digital Employee - Skills Module
项目经理数字员工系统 - Skill插件模块

包含10个核心Skill实现，每个Skill独立文件。
v1.3.0新增：文档解析相关Skill
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

# Module-level imports for Skill classes
from app.skills.project_overview_skill import ProjectOverviewSkill
from app.skills.weekly_report_skill import WeeklyReportSkill
from app.skills.policy_qa_skill import PolicyQASkill
from app.skills.task_update_skill import TaskUpdateSkill
from app.skills.risk_alert_skill import RiskAlertSkill
from app.skills.cost_monitor_skill import CostMonitorSkill
from app.skills.additional_skills import (
    WBSGenerationSkill,
    ProjectQuerySkill,
    MeetingMinutesSkill,
    ComplianceReviewSkill,
)

# v1.3.0新增：文档解析相关Skill
from app.skills.document_parse_skill import DocumentParseSkill, DocumentConfirmSkill


def register_all_skills() -> None:
    """注册所有Skill到Registry."""
    from app.orchestrator.skill_registry import register_skill

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
        # v1.3.0新增
        "document_parse": DocumentParseSkill,
        "document_confirm": DocumentConfirmSkill,
    }

    for skill_name, manifest in DEFAULT_SKILL_MANIFESTS.items():
        skill_class = skill_classes.get(skill_name)
        register_skill(manifest, skill_class)

    # 注册v1.3.0新增Skill
    register_skill(DocumentParseSkill.get_manifest(), DocumentParseSkill)
    register_skill(DocumentConfirmSkill.get_manifest(), DocumentConfirmSkill)


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
    # Skill类导出
    "ProjectOverviewSkill",
    "WeeklyReportSkill",
    "PolicyQASkill",
    "TaskUpdateSkill",
    "RiskAlertSkill",
    "CostMonitorSkill",
    "WBSGenerationSkill",
    "ProjectQuerySkill",
    "MeetingMinutesSkill",
    "ComplianceReviewSkill",
    # v1.3.0新增
    "DocumentParseSkill",
    "DocumentConfirmSkill",
]