"""
PM Digital Employee - Domain Enums Module
PM Digital Employee System - Domain enum definitions

Defines all business enum types for type safety and code readability.
Lark as the primary user interaction entrypoint.
"""

from enum import Enum, IntEnum


class UserRole(str, Enum):
    """用户角色枚举."""

    PROJECT_MANAGER = "project_manager"  # 项目经理
    PM = "pm"  # PMO/项目管理员
    TECH_LEAD = "tech_lead"  # 技术负责人
    MEMBER = "member"  # 项目成员
    AUDITOR = "auditor"  # 审计员
    ADMIN = "admin"  # 系统管理员


class ProjectStatus(str, Enum):
    """项目状态枚举."""

    DRAFT = "draft"  # 草稿
    PRE_INITIATION = "pre_initiation"  # 预立项
    INITIATED = "initiated"  # 已立项
    IN_PROGRESS = "in_progress"  # 进行中
    SUSPENDED = "suspended"  # 暂停
    COMPLETED = "completed"  # 已完成
    CLOSED = "closed"  # 已关闭
    ARCHIVED = "archived"  # 已归档


class TaskStatus(str, Enum):
    """任务状态枚举."""

    PENDING = "pending"  # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    DELAYED = "delayed"  # 已延期
    CANCELLED = "cancelled"  # 已取消
    BLOCKED = "blocked"  # 被阻塞


class TaskPriority(str, Enum):
    """任务优先级枚举."""

    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 紧急


class MilestoneStatus(str, Enum):
    """里程碑状态枚举."""

    PLANNED = "planned"  # 计划中
    IN_PROGRESS = "in_progress"  # 进行中
    ACHIEVED = "achieved"  # 已达成
    DELAYED = "delayed"  # 已延期
    CANCELLED = "cancelled"  # 已取消


class RiskLevel(str, Enum):
    """风险等级枚举."""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


class RiskStatus(str, Enum):
    """风险状态枚举."""

    IDENTIFIED = "identified"  # 已识别
    ANALYZING = "analyzing"  # 分析中
    MITIGATING = "mitigating"  # 处理中
    RESOLVED = "resolved"  # 已解决
    ACCEPTED = "accepted"  # 已接受
    CLOSED = "closed"  # 已关闭


class RiskCategory(str, Enum):
    """风险类别枚举."""

    SCHEDULE = "schedule"  # 进度风险
    COST = "cost"  # 成本风险
    RESOURCE = "resource"  # 资源风险
    QUALITY = "quality"  # 质量风险
    TECHNICAL = "technical"  # 技术风险
    COMPLIANCE = "compliance"  # 合规风险
    EXTERNAL = "external"  # 外部风险


class DocumentType(str, Enum):
    """文档类型枚举."""

    REQUIREMENT = "requirement"  # 需求文档
    DESIGN = "design"  # 设计文档
    REPORT = "report"  # 报告
    MINUTES = "minutes"  # 会议纪要
    CONTRACT = "contract"  # 合同
    PROPOSAL = "proposal"  # 立项材料
    WBS = "wbs"  # WBS文档
    RISK = "risk"  # 风险文档
    OTHER = "other"  # 其他


class DocumentStatus(str, Enum):
    """文档状态枚举."""

    DRAFT = "draft"  # 草稿
    UNDER_REVIEW = "under_review"  # 审核中
    APPROVED = "approved"  # 已批准
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档


class ApprovalStatus(str, Enum):
    """审批状态枚举."""

    PENDING = "pending"  # 待审批
    IN_PROGRESS = "in_progress"  # 审批中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消


class ApprovalType(str, Enum):
    """审批类型枚举."""

    PRE_INITIATION = "pre_initiation"  # 预立项审批
    INITIATION = "initiation"  # 立项审批
    CHANGE = "change"  # 变更审批
    BUDGET = "budget"  # 预算审批
    MILESTONE = "milestone"  # 里程碑审批
    COMPLETION = "completion"  # 完工审批


class PermissionAction(str, Enum):
    """权限动作枚举."""

    READ = "read"  # 读取
    WRITE = "write"  # 写入
    SUBMIT = "submit"  # 提交
    APPROVE = "approve"  # 审批
    EXECUTE = "execute"  # 执行
    MANAGE = "manage"  # 管理
    DELETE = "delete"  # 删除


class PermissionResource(str, Enum):
    """权限资源枚举."""

    PROJECT = "project"  # 项目
    TASK = "task"  # 任务
    MILESTONE = "milestone"  # 里程碑
    COST = "cost"  # 成本
    RISK = "risk"  # 风险
    DOCUMENT = "document"  # 文档
    REPORT = "report"  # 报告
    APPROVAL = "approval"  # 审批
    KNOWLEDGE = "knowledge"  # 知识库
    SKILL = "skill"  # 技能


class EventType(str, Enum):
    """事件类型枚举."""

    # 任务相关事件
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELAYED = "task.delayed"

    # 里程碑相关事件
    MILESTONE_CREATED = "milestone.created"
    MILESTONE_ACHIEVED = "milestone.achieved"
    MILESTONE_DELAYED = "milestone.delayed"

    # 成本相关事件
    COST_OVER_BUDGET = "cost.over_budget"
    COST_WARNING = "cost.warning"

    # 风险相关事件
    RISK_DETECTED = "risk.detected"
    RISK_UPDATED = "risk.updated"
    RISK_RESOLVED = "risk.resolved"

    # 报告相关事件
    REPORT_GENERATED = "report.generated"

    # 审批相关事件
    APPROVAL_PENDING = "approval.pending"
    APPROVAL_COMPLETED = "approval.completed"
    APPROVAL_REJECTED = "approval.rejected"

    # 会议相关事件
    MEETING_MINUTES_GENERATED = "meeting.minutes_generated"
    MEETING_TODO_OVERDUE = "meeting.todo_overdue"


class EventStatus(str, Enum):
    """事件状态枚举."""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    RETRY = "retry"  # 重试中


class KnowledgeScopeType(str, Enum):
    """知识库范围类型枚举."""

    PUBLIC = "public"  # 全行公开
    DEPARTMENT = "department"  # 部门内可见
    PROJECT = "project"  # 项目内可见
    CONFIDENTIAL = "confidential"  # 机密（仅授权人可见）


class ConversationRole(str, Enum):
    """对话角色枚举."""

    USER = "user"  # 用户
    ASSISTANT = "assistant"  # 助手
    SYSTEM = "system"  # 系统


class DialogState(str, Enum):
    """对话状态枚举."""

    ACTIVE = "active"  # 活跃
    COMPLETED = "completed"  # 已完成
    TIMEOUT = "timeout"  # 已超时
    CANCELLED = "cancelled"  # 已取消


class SkillExecutionStatus(str, Enum):
    """Skill执行状态枚举."""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    TIMEOUT = "timeout"  # 超时
    CANCELLED = "cancelled"  # 已取消


class CostCategory(str, Enum):
    """成本类别枚举."""

    LABOR = "labor"  # 人力成本
    EQUIPMENT = "equipment"  # 设备成本
    SOFTWARE = "software"  # 软件成本
    OUTSOURCING = "outsourcing"  # 外包成本
    TRAINING = "training"  # 培训成本
    TRAVEL = "travel"  # 差旅成本
    OTHER = "other"  # 其他成本


class AuditAction(str, Enum):
    """审计动作枚举."""

    # 用户操作
    LOGIN = "login"
    LOGOUT = "logout"

    # 数据操作
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # 权限操作
    GRANT_PERMISSION = "grant_permission"
    REVOKE_PERMISSION = "revoke_permission"

    # Skill操作
    EXECUTE_SKILL = "execute_skill"

    # LLM操作
    LLM_REQUEST = "llm_request"

    # RAG操作
    RAG_QUERY = "rag_query"

    # 安全操作
    SECURITY_BLOCK = "security_block"
    SECURITY_ALERT = "security_alert"


class IntegrationSystem(str, Enum):
    """Integration system enums."""

    LARK = "lark"  # Lark/Feishu
    PROJECT_SYSTEM = "project_system"  # Project Management System
    FINANCE_SYSTEM = "finance_system"  # Finance System
    DEVOPS_SYSTEM = "devops_system"  # DevOps System
    DEFECT_SYSTEM = "defect_system"  # Defect System
    OA_SYSTEM = "oa_system"  # OA Approval System


# ============================================
# v1.2.0新增：多源数据录入相关枚举
# ============================================


class DataSource(str, Enum):
    """数据来源类型枚举."""

    LARK_CARD = "lark_card"           # 飞书卡片录入
    EXCEL_IMPORT = "excel_import"     # Excel模板导入
    LARK_SHEET_SYNC = "lark_sheet_sync"  # 飞书在线表格同步
    SYSTEM_GENERATED = "system_generated"  # 系统自动生成
    DOCUMENT_PARSE = "document_parse"  # 文档智能解析（v1.3.0新增）


class SyncMode(str, Enum):
    """同步模式枚举."""

    TO_SHEET = "to_sheet"             # 单向：系统→飞书表格
    FROM_SHEET = "from_sheet"         # 单向：飞书表格→系统
    BIDIRECTIONAL = "bidirectional"   # 双向同步


class SyncFrequency(str, Enum):
    """同步频率枚举."""

    REALTIME = "realtime"             # 实时（Webhook触发）
    FIVE_MINUTES = "5min"             # 每5分钟
    FIFTEEN_MINUTES = "15min"         # 每15分钟
    ONE_HOUR = "1hour"                # 每小时


class ImportMode(str, Enum):
    """Excel导入模式枚举."""

    FULL_REPLACE = "full_replace"     # 全量替换
    INCREMENTAL_UPDATE = "incremental_update"  # 增量更新
    APPEND_ONLY = "append_only"       # 仅追加


class DependencyType(str, Enum):
    """任务依赖类型枚举."""

    FS = "fs"  # 完成-开始 (Finish-to-Start)
    SS = "ss"  # 开始-开始 (Start-to-Start)
    FF = "ff"  # 完成-完成 (Finish-to-Finish)
    SF = "sf"  # 开始-完成 (Start-to-Finish)


class WeeklyReportStatus(str, Enum):
    """周报状态枚举."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ARCHIVED = "archived"


class MeetingStatus(str, Enum):
    """会议纪要状态枚举."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class WBSStatus(str, Enum):
    """WBS状态枚举."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ============================================
# v1.3.0新增：文档智能解析相关枚举
# ============================================


class DocumentParseStatus(str, Enum):
    """文档解析状态枚举."""

    PENDING = "pending"           # 待处理
    DOWNLOADING = "downloading"   # 下载文件
    PARSING = "parsing"           # 解析内容
    CLASSIFYING = "classifying"   # 分类识别
    EXTRACTING = "extracting"     # 信息提取
    VALIDATING = "validating"     # 数据校验
    IMPORTING = "importing"       # 入库中
    CONFIRMING = "confirming"     # 待确认
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class DocumentImportStatus(str, Enum):
    """文档入库状态枚举."""

    PENDING = "pending"           # 待入库
    SUCCESS = "success"           # 入库成功
    PARTIAL = "partial"           # 部分成功
    FAILED = "failed"             # 入库失败
    CONFLICT = "conflict"         # 存在冲突
    SKIPPED = "skipped"           # 已跳过


class DocumentCategory(str, Enum):
    """文档大类枚举."""

    PROJECT_DOC = "project_doc"       # 项目文档
    MANAGEMENT_DOC = "management_doc" # 管理文档
    EXTERNAL_DOC = "external_doc"     # 外部文档
    OTHER = "other"                   # 其他


class ProjectPhase(str, Enum):
    """项目阶段枚举（用于文档分类）."""

    PRE_INITIATION = "pre_initiation"  # 预立项阶段
    INITIATION = "initiation"          # 立项阶段
    EXECUTION = "execution"            # 执行阶段
    CLOSING = "closing"                # 收尾阶段
    FULL_CYCLE = "full_cycle"          # 全周期文档
    NONE = "none"                      # 无特定阶段


class DocumentSubtype(str, Enum):
    """文档子类型枚举."""

    # 预立项阶段
    PROJECT_PROPOSAL = "project_proposal"      # 项目建议书
    FEASIBILITY_REPORT = "feasibility_report"  # 可行性研究报告
    INITIATION_APPROVAL = "initiation_approval"  # 立项批复

    # 立项阶段
    INITIATION_DOC = "initiation_doc"          # 立项审批材料
    PROJECT_CHARTER = "project_charter"        # 项目章程

    # 执行阶段
    WEEKLY_REPORT = "weekly_report"            # 周报
    MEETING_MINUTES = "meeting_minutes"        # 会议纪要
    TASK_REPORT = "task_report"                # 任务报告
    PROGRESS_REPORT = "progress_report"        # 进度报告

    # 收尾阶段
    ACCEPTANCE_REPORT = "acceptance_report"    # 验收报告
    SUMMARY_REPORT = "summary_report"          # 项目总结
    REVIEW_DOC = "review_doc"                  # 复盘文档

    # 全周期
    WBS = "wbs"                                # WBS工作分解
    RISK_REGISTER = "risk_register"            # 风险登记表
    COST_REPORT = "cost_report"                # 成本报告
    MILESTONE_PLAN = "milestone_plan"          # 里程碑计划

    # 管理文档
    POLICY_DOC = "policy_doc"                  # 管理制度
    STANDARD_DOC = "standard_doc"              # 操作规范
    PROCESS_DOC = "process_doc"                # 流程文档

    # 外部文档
    CONTRACT = "contract"                      # 合同文件
    SUPPLIER_DOC = "supplier_doc"              # 供应商材料
    EXTERNAL_REPORT = "external_report"        # 外部报告

    # 其他
    UNKNOWN = "unknown"                        # 未识别类型


class ConflictResolutionStrategy(str, Enum):
    """冲突解决策略枚举."""

    MANUAL = "manual"               # 人工确认
    LAST_WRITE = "last_write"       # 时间戳最新优先
    SOURCE_PRIORITY = "source_priority"  # 来源优先级
    USER_DECISION = "user_decision" # 用户决定


class ConfirmationAction(str, Enum):
    """用户确认动作枚举."""

    CONFIRM = "confirm"             # 确认入库
    EDIT = "edit"                   # 修改数据
    CANCEL = "cancel"               # 取消
    RESOLVE_NEW = "resolve_new"     # 冲突采用新数据
    RESOLVE_EXISTING = "resolve_existing"  # 冲突保留原数据
    RESOLVE_MANUAL = "resolve_manual"  # 冲突人工编辑