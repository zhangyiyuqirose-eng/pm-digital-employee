"""
PM Digital Employee - Presentation Module
项目经理数字员工系统 - 展示层模块
"""

from app.presentation.cards import (
    BaseCard,
    ProjectOverviewCard,
    RiskAlertCard,
    WeeklyReportCard,
    ClarificationCard,
    TaskUpdateCard,
    ApprovalStatusCard,
    ErrorCard,
    SuccessCard,
    create_card,
    CARD_CLASSES,
)
from app.presentation.renderers import (
    ResultRenderer,
    ProjectDataRenderer,
    ReportRenderer,
    get_result_renderer,
    get_project_renderer,
    get_report_renderer,
)

__all__ = [
    "BaseCard",
    "ProjectOverviewCard",
    "RiskAlertCard",
    "WeeklyReportCard",
    "ClarificationCard",
    "TaskUpdateCard",
    "ApprovalStatusCard",
    "ErrorCard",
    "SuccessCard",
    "create_card",
    "CARD_CLASSES",
    "ResultRenderer",
    "ProjectDataRenderer",
    "ReportRenderer",
    "get_result_renderer",
    "get_project_renderer",
    "get_report_renderer",
]