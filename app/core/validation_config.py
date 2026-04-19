"""
PM Digital Employee - Validation Config
项目经理数字员工系统 - 校验配置模块

定义各模块的校验规则配置，包括必填字段、数据类型和业务规则。
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class FieldValidationConfig(BaseModel):
    """字段校验配置."""

    field_name: str              # 字段名称（英文）
    display_name: str            # 字段显示名称（中文）
    field_type: str              # 数据类型：str, int, float, date, datetime, bool, enum
    required: bool = False       # 是否必填
    min_value: Optional[float] = None    # 最小值（用于数值类型）
    max_value: Optional[float] = None    # 最大值（用于数值类型）
    min_length: Optional[int] = None     # 最小长度（用于字符串类型）
    max_length: Optional[int] = None     # 最大长度（用于字符串类型）
    enum_values: Optional[List[str]] = None  # 枚举允许值
    pattern: Optional[str] = None        # 正则表达式校验


class BusinessRuleConfig(BaseModel):
    """业务规则配置."""

    rule_name: str               # 规则名称
    rule_type: str               # 规则类型：compare, range, custom
    description: str             # 规则描述
    fields: List[str]            # 涉及的字段列表
    params: Optional[Dict[str, Any]] = None  # 规则参数


class ModuleValidationConfig(BaseModel):
    """模块校验配置."""

    module_name: str             # 模块名称
    display_name: str            # 模块显示名称（中文）
    fields: List[FieldValidationConfig]    # 字段校验配置列表
    business_rules: List[BusinessRuleConfig] = []  # 业务规则配置列表


# ============================================
# 项目模块校验配置
# ============================================

PROJECT_MODULE_CONFIG = ModuleValidationConfig(
    module_name="project",
    display_name="项目",
    fields=[
        FieldValidationConfig(
            field_name="name",
            display_name="项目名称",
            field_type="str",
            required=True,
            min_length=1,
            max_length=200,
        ),
        FieldValidationConfig(
            field_name="code",
            display_name="项目编码",
            field_type="str",
            required=False,
            min_length=1,
            max_length=50,
        ),
        FieldValidationConfig(
            field_name="project_type",
            display_name="项目类型",
            field_type="enum",
            required=True,
            enum_values=["研发项目", "运维项目", "工程项目", "其他项目"],
        ),
        FieldValidationConfig(
            field_name="start_date",
            display_name="计划开始日期",
            field_type="date",
            required=False,
        ),
        FieldValidationConfig(
            field_name="end_date",
            display_name="计划结束日期",
            field_type="date",
            required=False,
        ),
        FieldValidationConfig(
            field_name="total_budget",
            display_name="总预算",
            field_type="float",
            required=False,
            min_value=0,
        ),
        FieldValidationConfig(
            field_name="status",
            display_name="项目状态",
            field_type="enum",
            required=False,
            enum_values=["draft", "pre_initiation", "initiated", "in_progress",
                         "suspended", "completed", "closed", "archived"],
        ),
    ],
    business_rules=[
        BusinessRuleConfig(
            rule_name="project_end_date_after_start",
            rule_type="compare",
            description="项目结束日期必须大于或等于开始日期",
            fields=["start_date", "end_date"],
            params={"operator": ">=", "allow_equal": True},
        ),
        BusinessRuleConfig(
            rule_name="project_budget_positive",
            rule_type="range",
            description="项目预算必须大于等于0",
            fields=["total_budget"],
            params={"min": 0},
        ),
    ],
)


# ============================================
# 任务模块校验配置
# ============================================

TASK_MODULE_CONFIG = ModuleValidationConfig(
    module_name="task",
    display_name="任务",
    fields=[
        FieldValidationConfig(
            field_name="name",
            display_name="任务名称",
            field_type="str",
            required=True,
            min_length=1,
            max_length=200,
        ),
        FieldValidationConfig(
            field_name="project_id",
            display_name="项目ID",
            field_type="str",
            required=True,
        ),
        FieldValidationConfig(
            field_name="start_date",
            display_name="开始日期",
            field_type="date",
            required=False,
        ),
        FieldValidationConfig(
            field_name="end_date",
            display_name="截止日期",
            field_type="date",
            required=False,
        ),
        FieldValidationConfig(
            field_name="priority",
            display_name="优先级",
            field_type="enum",
            required=False,
            enum_values=["low", "medium", "high", "critical"],
        ),
        FieldValidationConfig(
            field_name="status",
            display_name="任务状态",
            field_type="enum",
            required=False,
            enum_values=["pending", "in_progress", "completed", "delayed",
                         "cancelled", "blocked"],
        ),
        FieldValidationConfig(
            field_name="estimated_hours",
            display_name="预估工时",
            field_type="float",
            required=False,
            min_value=0,
        ),
        FieldValidationConfig(
            field_name="actual_hours",
            display_name="实际工时",
            field_type="float",
            required=False,
            min_value=0,
        ),
        FieldValidationConfig(
            field_name="progress",
            display_name="进度",
            field_type="int",
            required=False,
            min_value=0,
            max_value=100,
        ),
    ],
    business_rules=[
        BusinessRuleConfig(
            rule_name="task_end_date_after_start",
            rule_type="compare",
            description="任务截止日期必须大于或等于开始日期",
            fields=["start_date", "end_date"],
            params={"operator": ">=", "allow_equal": True},
        ),
        BusinessRuleConfig(
            rule_name="task_hours_positive",
            rule_type="range",
            description="工时必须大于等于0",
            fields=["estimated_hours", "actual_hours"],
            params={"min": 0},
        ),
        BusinessRuleConfig(
            rule_name="task_progress_range",
            rule_type="range",
            description="进度必须在0-100之间",
            fields=["progress"],
            params={"min": 0, "max": 100},
        ),
    ],
)


# ============================================
# 里程碑模块校验配置
# ============================================

MILESTONE_MODULE_CONFIG = ModuleValidationConfig(
    module_name="milestone",
    display_name="里程碑",
    fields=[
        FieldValidationConfig(
            field_name="name",
            display_name="里程碑名称",
            field_type="str",
            required=True,
            min_length=1,
            max_length=200,
        ),
        FieldValidationConfig(
            field_name="project_id",
            display_name="项目ID",
            field_type="str",
            required=True,
        ),
        FieldValidationConfig(
            field_name="planned_date",
            display_name="计划日期",
            field_type="date",
            required=True,
        ),
        FieldValidationConfig(
            field_name="status",
            display_name="里程碑状态",
            field_type="enum",
            required=False,
            enum_values=["planned", "in_progress", "achieved", "delayed", "cancelled"],
        ),
    ],
    business_rules=[
        BusinessRuleConfig(
            rule_name="milestone_date_valid",
            rule_type="range",
            description="里程碑计划日期必须有效",
            fields=["planned_date"],
            params={},
        ),
    ],
)


# ============================================
# 风险模块校验配置
# ============================================

RISK_MODULE_CONFIG = ModuleValidationConfig(
    module_name="risk",
    display_name="风险",
    fields=[
        FieldValidationConfig(
            field_name="title",
            display_name="风险标题",
            field_type="str",
            required=True,
            min_length=1,
            max_length=200,
        ),
        FieldValidationConfig(
            field_name="project_id",
            display_name="项目ID",
            field_type="str",
            required=True,
        ),
        FieldValidationConfig(
            field_name="level",
            display_name="风险等级",
            field_type="enum",
            required=True,
            enum_values=["low", "medium", "high", "critical"],
        ),
        FieldValidationConfig(
            field_name="category",
            display_name="风险类别",
            field_type="enum",
            required=False,
            enum_values=["schedule", "cost", "resource", "quality",
                         "technical", "compliance", "external"],
        ),
        FieldValidationConfig(
            field_name="status",
            display_name="风险状态",
            field_type="enum",
            required=False,
            enum_values=["identified", "analyzing", "mitigating",
                         "resolved", "accepted", "closed"],
        ),
        FieldValidationConfig(
            field_name="probability",
            display_name="发生概率",
            field_type="int",
            required=False,
            min_value=1,
            max_value=5,
        ),
        FieldValidationConfig(
            field_name="impact",
            display_name="影响程度",
            field_type="int",
            required=False,
            min_value=1,
            max_value=5,
        ),
    ],
    business_rules=[
        BusinessRuleConfig(
            rule_name="risk_probability_range",
            rule_type="range",
            description="风险发生概率必须在1-5之间",
            fields=["probability"],
            params={"min": 1, "max": 5},
        ),
        BusinessRuleConfig(
            rule_name="risk_impact_range",
            rule_type="range",
            description="风险影响程度必须在1-5之间",
            fields=["impact"],
            params={"min": 1, "max": 5},
        ),
    ],
)


# ============================================
# 成本模块校验配置
# ============================================

COST_MODULE_CONFIG = ModuleValidationConfig(
    module_name="cost",
    display_name="成本",
    fields=[
        FieldValidationConfig(
            field_name="project_id",
            display_name="项目ID",
            field_type="str",
            required=True,
        ),
        FieldValidationConfig(
            field_name="category",
            display_name="成本类别",
            field_type="enum",
            required=True,
            enum_values=["labor", "equipment", "software", "outsourcing",
                         "training", "travel", "other"],
        ),
        FieldValidationConfig(
            field_name="amount",
            display_name="金额",
            field_type="float",
            required=True,
            min_value=0,
        ),
        FieldValidationConfig(
            field_name="description",
            display_name="描述",
            field_type="str",
            required=False,
            max_length=500,
        ),
    ],
    business_rules=[
        BusinessRuleConfig(
            rule_name="cost_amount_positive",
            rule_type="range",
            description="成本金额必须大于等于0",
            fields=["amount"],
            params={"min": 0},
        ),
    ],
)


# ============================================
# 模块配置映射表
# ============================================

MODULE_CONFIGS: Dict[str, ModuleValidationConfig] = {
    "project": PROJECT_MODULE_CONFIG,
    "task": TASK_MODULE_CONFIG,
    "milestone": MILESTONE_MODULE_CONFIG,
    "risk": RISK_MODULE_CONFIG,
    "cost": COST_MODULE_CONFIG,
}


def get_module_config(module: str) -> Optional[ModuleValidationConfig]:
    """
    获取指定模块的校验配置.

    Args:
        module: 模块名称

    Returns:
        ModuleValidationConfig: 模块校验配置，如果不存在则返回None
    """
    return MODULE_CONFIGS.get(module)


def get_all_module_names() -> List[str]:
    """
    获取所有已配置的模块名称列表.

    Returns:
        List[str]: 模块名称列表
    """
    return list(MODULE_CONFIGS.keys())