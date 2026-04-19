"""
PM Digital Employee - Domain Models Module
项目经理数字员工系统 - 领域模型初始化

导出所有ORM模型，供其他模块使用。
v1.2.0新增：多源数据录入相关模型
"""

from app.domain.models.user import User
from app.domain.models.project import Project
from app.domain.models.user_project_role import UserProjectRole
from app.domain.models.group_project_binding import GroupProjectBinding
from app.domain.models.task import Task
from app.domain.models.milestone import Milestone
from app.domain.models.cost import ProjectCostBudget, ProjectCostActual
from app.domain.models.risk import ProjectRisk
from app.domain.models.document import ProjectDocument
from app.domain.models.conversation import ConversationSession, ConversationMessage
from app.domain.models.skill_definition import SkillDefinition, ProjectSkillSwitch
from app.domain.models.approval import ApprovalWorkflow
from app.domain.models.audit_log import AuditLog
from app.domain.models.knowledge import KnowledgeDocument, RetrievalTrace
from app.domain.models.event_record import EventRecord
from app.domain.models.llm_usage_log import LLMUsageLog

# v1.2.0新增模型
from app.domain.models.weekly_report import WeeklyReport
from app.domain.models.meeting_minutes import MeetingMinutes
from app.domain.models.wbs_version import WBSVersion
from app.domain.models.data_sync_log import DataSyncLog
from app.domain.models.excel_import_log import ExcelImportLog
from app.domain.models.lark_sheet_binding import LarkSheetBinding
from app.domain.models.data_version import DataVersion
from app.domain.models.data_conflict import DataConflict

__all__ = [
    "User",
    "Project",
    "UserProjectRole",
    "GroupProjectBinding",
    "Task",
    "Milestone",
    "ProjectCostBudget",
    "ProjectCostActual",
    "ProjectRisk",
    "ProjectDocument",
    "ConversationSession",
    "ConversationMessage",
    "SkillDefinition",
    "ProjectSkillSwitch",
    "ApprovalWorkflow",
    "AuditLog",
    "KnowledgeDocument",
    "RetrievalTrace",
    "EventRecord",
    "LLMUsageLog",
    # v1.2.0新增
    "WeeklyReport",
    "MeetingMinutes",
    "WBSVersion",
    "DataSyncLog",
    "ExcelImportLog",
    "LarkSheetBinding",
    "DataVersion",
    "DataConflict",
]