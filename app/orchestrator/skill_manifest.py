"""
PM Digital Employee - Skill Manifest
项目经理数字员工系统 - Skill Manifest规范定义

定义Skill的标准Manifest格式，用于Skill注册、发现、调用。
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.orchestrator.schemas import SkillManifest


class InputParamSchema(BaseModel):
    """输入参数Schema."""

    type: str = Field("string", description="参数类型")
    description: str = Field("", description="参数描述")
    required: bool = Field(True, description="是否必填")
    default: Optional[Any] = Field(None, description="默认值")
    enum: Optional[List[str]] = Field(None, description="枚举值列表")
    min_value: Optional[int] = Field(None, description="最小值")
    max_value: Optional[int] = Field(None, description="最大值")
    pattern: Optional[str] = Field(None, description="正则校验")
    examples: List[str] = Field(default_factory=list, description="示例值")


class OutputFieldSchema(BaseModel):
    """输出字段Schema."""

    type: str = Field("string", description="字段类型")
    description: str = Field("", description="字段描述")


class PermissionRequirement(BaseModel):
    """权限需求."""

    resource: str = Field(..., description="资源类型: project/task/cost/risk")
    action: str = Field(..., description="操作类型: read/write/delete")
    scope: str = Field("project", description="权限范围: project/global")


class SkillManifestBuilder:
    """
    Skill Manifest构建器.

    提供便捷方法构建标准化的Skill Manifest。
    """

    def __init__(self) -> None:
        """初始化构建器."""
        self._skill_name: str = ""
        self._display_name: str = ""
        self._description: str = ""
        self._version: str = "1.0.0"
        self._domain: str = "general"
        self._input_params: Dict[str, InputParamSchema] = {}
        self._output_fields: Dict[str, OutputFieldSchema] = {}
        self._allowed_roles: List[str] = []
        self._required_permissions: List[PermissionRequirement] = []
        self._enabled_by_default: bool = True
        self._supports_async: bool = False
        self._supports_confirmation: bool = False
        self._dependencies: List[str] = []

    def set_name(self, skill_name: str, display_name: str) -> "SkillManifestBuilder":
        """
        设置Skill名称.

        Args:
            skill_name: Skill唯一标识（英文下划线）
            display_name: 显示名称（中文）

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._skill_name = skill_name
        self._display_name = display_name
        return self

    def set_description(self, description: str) -> "SkillManifestBuilder":
        """
        设置功能描述.

        Args:
            description: 功能详细描述（用于意图识别）

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._description = description
        return self

    def set_version(self, version: str) -> "SkillManifestBuilder":
        """
        设置版本号.

        Args:
            version: 语义化版本号

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._version = version
        return self

    def set_domain(self, domain: str) -> "SkillManifestBuilder":
        """
        设置业务域.

        Args:
            domain: 所属业务域

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._domain = domain
        return self

    def add_input_param(
        self,
        name: str,
        type: str = "string",
        description: str = "",
        required: bool = True,
        default: Optional[Any] = None,
        enum: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
    ) -> "SkillManifestBuilder":
        """
        添加输入参数.

        Args:
            name: 参数名
            type: 参数类型
            description: 参数描述
            required: 是否必填
            default: 默认值
            enum: 枚举值
            examples: 示例值

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._input_params[name] = InputParamSchema(
            type=type,
            description=description,
            required=required,
            default=default,
            enum=enum,
            examples=examples or [],
        )
        return self

    def add_output_field(
        self,
        name: str,
        type: str = "string",
        description: str = "",
    ) -> "SkillManifestBuilder":
        """
        添加输出字段.

        Args:
            name: 字段名
            type: 字段类型
            description: 字段描述

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._output_fields[name] = OutputFieldSchema(
            type=type,
            description=description,
        )
        return self

    def set_allowed_roles(
        self,
        roles: List[str],
    ) -> "SkillManifestBuilder":
        """
        设置允许的角色.

        Args:
            roles: 角色列表

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._allowed_roles = roles
        return self

    def add_permission(
        self,
        resource: str,
        action: str,
        scope: str = "project",
    ) -> "SkillManifestBuilder":
        """
        添加权限需求.

        Args:
            resource: 资源类型
            action: 操作类型
            scope: 权限范围

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._required_permissions.append(
            PermissionRequirement(
                resource=resource,
                action=action,
                scope=scope,
            ),
        )
        return self

    def set_enabled_by_default(
        self,
        enabled: bool,
    ) -> "SkillManifestBuilder":
        """
        设置默认启用状态.

        Args:
            enabled: 是否默认启用

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._enabled_by_default = enabled
        return self

    def set_async_support(
        self,
        supports_async: bool,
    ) -> "SkillManifestBuilder":
        """
        设置异步执行支持.

        Args:
            supports_async: 是否支持异步

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._supports_async = supports_async
        return self

    def set_confirmation_support(
        self,
        supports_confirmation: bool,
    ) -> "SkillManifestBuilder":
        """
        设置确认支持.

        Args:
            supports_confirmation: 是否需要确认

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._supports_confirmation = supports_confirmation
        return self

    def add_dependency(
        self,
        skill_name: str,
    ) -> "SkillManifestBuilder":
        """
        添加依赖Skill.

        Args:
            skill_name: 依赖的Skill名称

        Returns:
            SkillManifestBuilder: 构建器实例
        """
        self._dependencies.append(skill_name)
        return self

    def build(self) -> SkillManifest:
        """
        构建Skill Manifest.

        Returns:
            SkillManifest: Manifest对象
        """
        # 构建input_schema
        input_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        for name, param in self._input_params.items():
            prop: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                prop["default"] = param.default
            if param.enum:
                prop["enum"] = param.enum
            if param.pattern:
                prop["pattern"] = param.pattern
            if param.min_value is not None:
                prop["minimum"] = param.min_value
            if param.max_value is not None:
                prop["maximum"] = param.max_value
            input_schema["properties"][name] = prop
            if param.required:
                input_schema["required"].append(name)

        # 构建output_schema
        output_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
        }
        for name, field in self._output_fields.items():
            output_schema["properties"][name] = {
                "type": field.type,
                "description": field.description,
            }

        # 构建permissions
        permissions: List[Dict[str, str]] = [
            {
                "resource": p.resource,
                "action": p.action,
                "scope": p.scope,
            }
            for p in self._required_permissions
        ]

        return SkillManifest(
            skill_name=self._skill_name,
            display_name=self._display_name,
            description=self._description,
            version=self._version,
            domain=self._domain,
            input_schema=input_schema,
            output_schema=output_schema,
            allowed_roles=self._allowed_roles or ["project_manager", "pm", "tech_lead", "member"],
            required_permissions=permissions,
            enabled_by_default=self._enabled_by_default,
            supports_async=self._supports_async,
            supports_confirmation=self._supports_confirmation,
            dependencies=self._dependencies,
        )

    def build_json(self) -> str:
        """
        构建JSON格式的Manifest.

        Returns:
            str: JSON字符串
        """
        manifest = self.build()
        return json.dumps(
            manifest.model_dump(exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )


# ==================== 预定义Skill Manifest ====================


def get_project_overview_manifest() -> SkillManifest:
    """获取项目总览Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("project_overview", "项目总览查询")
    builder.set_description(
        "查询项目的整体状态信息，包括进度、里程碑、风险、成本等。"
        "用户可以输入'查看项目状态'、'项目总览'、'项目概况'等触发。"
    )
    builder.set_domain("project")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID或项目名称",
        required=False,
        examples=["项目A", "2023-001"],
    )
    builder.add_output_field("project_name", description="项目名称")
    builder.add_output_field("status", description="项目状态")
    builder.add_output_field("progress", description="整体进度")
    builder.add_output_field("milestones", description="里程碑列表")
    builder.add_output_field("risks", description="风险列表")
    builder.add_output_field("cost_summary", description="成本摘要")
    builder.add_permission("project", "read")
    return builder.build()


def get_weekly_report_manifest() -> SkillManifest:
    """获取周报生成Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("weekly_report", "项目周报生成")
    builder.set_description(
        "自动生成项目周报，汇总本周任务进展、下周计划、风险状态等。"
        "用户可以输入'生成周报'、'本周周报'、'写周报'等触发。"
    )
    builder.set_domain("report")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=False,
    )
    builder.add_input_param(
        "week_start",
        type="string",
        description="周开始日期",
        required=False,
        examples=["本周", "上周", "2024-01-01"],
    )
    builder.add_output_field("report_content", description="周报内容")
    builder.add_output_field("tasks_completed", description="已完成任务")
    builder.add_output_field("tasks_in_progress", description="进行中任务")
    builder.add_output_field("next_week_plan", description="下周计划")
    builder.add_permission("project", "read")
    builder.add_permission("task", "read")
    builder.set_async_support(True)
    return builder.build()


def get_wbs_generation_manifest() -> SkillManifest:
    """获取WBS生成Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("wbs_generation", "WBS自动生成")
    builder.set_description(
        "根据项目信息自动生成WBS工作分解结构，包含任务分解、时间估算、依赖关系。"
        "用户可以输入'生成WBS'、'任务分解'、'工作分解'等触发。"
    )
    builder.set_domain("planning")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=True,
    )
    builder.add_input_param(
        "requirements",
        type="string",
        description="项目需求描述",
        required=False,
    )
    builder.add_output_field("wbs_structure", description="WBS结构")
    builder.add_output_field("task_count", description="任务数量")
    builder.add_output_field("estimated_duration", description="预估工期")
    builder.add_permission("project", "read")
    builder.add_permission("task", "write")
    builder.set_confirmation_support(True)
    builder.set_async_support(True)
    return builder.build()


def get_task_update_manifest() -> SkillManifest:
    """获取任务更新Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("task_update", "任务进度更新")
    builder.set_description(
        "更新任务进度状态，包括完成百分比、状态变更、备注添加。"
        "用户可以输入'更新任务进度'、'完成任务'、'任务状态'等触发。"
    )
    builder.set_domain("task")
    builder.add_input_param(
        "task_id",
        type="string",
        description="任务ID或任务名称",
        required=True,
    )
    builder.add_input_param(
        "progress",
        type="integer",
        description="进度百分比",
        required=False,
    )
    builder.add_input_param(
        "status",
        type="string",
        description="任务状态",
        required=False,
        enum=["pending", "in_progress", "completed", "blocked"],
    )
    builder.add_input_param(
        "notes",
        type="string",
        description="备注说明",
        required=False,
    )
    builder.add_output_field("task_id", description="任务ID")
    builder.add_output_field("updated_fields", description="更新的字段")
    builder.add_permission("task", "write")
    return builder.build()


def get_risk_alert_manifest() -> SkillManifest:
    """获取风险预警Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("risk_alert", "风险识别与预警")
    builder.set_description(
        "识别项目风险并发出预警，分析风险等级、影响范围、应对措施。"
        "用户可以输入'查看风险'、'风险预警'、'项目风险'等触发。"
    )
    builder.set_domain("risk")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=False,
    )
    builder.add_input_param(
        "risk_type",
        type="string",
        description="风险类型筛选",
        required=False,
    )
    builder.add_output_field("risks", description="风险列表")
    builder.add_output_field("high_risks", description="高风险项")
    builder.add_output_field("recommendations", description="应对建议")
    builder.add_permission("risk", "read")
    builder.add_permission("project", "read")
    return builder.build()


def get_cost_monitor_manifest() -> SkillManifest:
    """获取成本监控Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("cost_monitor", "成本监控")
    builder.set_description(
        "监控项目成本执行情况，对比预算与实际支出，预警超支风险。"
        "用户可以输入'查看成本'、'成本监控'、'预算情况'等触发。"
    )
    builder.set_domain("cost")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=False,
    )
    builder.add_output_field("budget_summary", description="预算摘要")
    builder.add_output_field("actual_costs", description="实际支出")
    builder.add_output_field("variance", description="偏差分析")
    builder.add_output_field("burn_rate", description="消耗速率")
    builder.add_permission("cost", "read")
    builder.add_permission("project", "read")
    return builder.build()


def get_policy_qa_manifest() -> SkillManifest:
    """获取制度规范问答Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("policy_qa", "项目制度规范答疑")
    builder.set_description(
        "回答项目管理规章制度相关问题，基于知识库检索并引用来源。"
        "用户可以输入'管理制度'、'流程规范'、'XX规定'等触发。"
    )
    builder.set_domain("knowledge")
    builder.add_input_param(
        "question",
        type="string",
        description="用户问题",
        required=True,
    )
    builder.add_output_field("answer", description="回答内容")
    builder.add_output_field("sources", description="引用来源")
    builder.add_output_field("confidence", description="回答置信度")
    return builder.build()


def get_project_query_manifest() -> SkillManifest:
    """获取项目情况咨询Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("project_query", "项目情况咨询")
    builder.set_description(
        "回答项目具体情况相关问题，如人员配置、进度偏差、里程碑等。"
        "用户可以输入'项目人员'、'进度怎么样'、'里程碑情况'等触发。"
    )
    builder.set_domain("project")
    builder.add_input_param(
        "question",
        type="string",
        description="用户问题",
        required=True,
    )
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=False,
    )
    builder.add_output_field("answer", description="回答内容")
    builder.add_output_field("data_summary", description="数据摘要")
    builder.add_permission("project", "read")
    return builder.build()


def get_meeting_minutes_manifest() -> SkillManifest:
    """获取会议纪要Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("meeting_minutes", "会议纪要生成")
    builder.set_description(
        "根据会议内容生成结构化会议纪要，包含议题、决议、待办事项。"
        "用户可以输入'会议纪要'、'生成纪要'、'会议记录'等触发。"
    )
    builder.set_domain("meeting")
    builder.add_input_param(
        "meeting_content",
        type="string",
        description="会议内容/记录",
        required=True,
    )
    builder.add_input_param(
        "meeting_title",
        type="string",
        description="会议标题",
        required=False,
    )
    builder.add_input_param(
        "participants",
        type="string",
        description="参会人员",
        required=False,
    )
    builder.add_output_field("meeting_title", description="会议标题")
    builder.add_output_field("agenda", description="议题列表")
    builder.add_output_field("decisions", description="决议")
    builder.add_output_field("action_items", description="待办事项")
    builder.add_permission("document", "write")
    builder.set_async_support(True)
    return builder.build()


def get_compliance_review_manifest() -> SkillManifest:
    """获取合规初审Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("compliance_review", "预立项/立项材料合规初审")
    builder.set_description(
        "审核预立项/立项材料的合规性，检查必填项、格式规范、内容完整性。"
        "用户可以输入'初审材料'、'合规检查'、'审核立项'等触发。"
    )
    builder.set_domain("compliance")
    builder.add_input_param(
        "document_id",
        type="string",
        description="文档ID",
        required=True,
    )
    builder.add_input_param(
        "document_type",
        type="string",
        description="文档类型",
        required=True,
        enum=["pre_initiation", "initiation", "change_request"],
    )
    builder.add_output_field("compliance_status", description="合规状态")
    builder.add_output_field("check_results", description="检查结果")
    builder.add_output_field("missing_items", description="缺失项")
    builder.add_output_field("suggestions", description="改进建议")
    builder.add_permission("document", "read")
    builder.add_permission("approval", "write")
    builder.set_confirmation_support(True)
    builder.set_async_support(True)
    return builder.build()


# ==================== 成本相关Skill Manifest ====================


def get_cost_estimation_manifest() -> SkillManifest:
    """获取成本估算Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("cost_estimation", "成本估算")
    builder.set_description(
        "基于需求文档进行IT项目工作量评估和成本估算，支持功能模块识别、人月计算、成本分布。"
        "用户可以输入'成本估算'、'工作量评估'、'项目估价'、'费用估算'等触发。"
    )
    builder.set_domain("cost")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=False,
    )
    builder.add_input_param(
        "project_name",
        type="string",
        description="项目名称",
        required=False,
    )
    builder.add_input_param(
        "type",
        type="string",
        description="估算类型",
        required=False,
        enum=["quick", "detailed"],
        default="quick",
    )
    builder.add_output_field("total_workload", description="总工作量(人天)")
    builder.add_output_field("total_person_months", description="总人月")
    builder.add_output_field("total_cost", description="总成本")
    builder.add_output_field("phase_workloads", description="阶段工作量分布")
    builder.add_output_field("team_costs", description="团队成本分布")
    builder.add_permission("cost", "read")
    builder.add_permission("project", "read")
    builder.set_async_support(True)
    return builder.build()


def get_cost_monitoring_manifest() -> SkillManifest:
    """获取成本监控(EVM)Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("cost_monitoring", "成本监控EVM")
    builder.set_description(
        "基于EVM挣值管理的成本监控，计算SPI/CPI绩效指标，预警成本偏差。"
        "用户可以输入'成本监控'、'挣值分析'、'EVM分析'、'成本绩效'等触发。"
    )
    builder.set_domain("cost")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=True,
    )
    builder.add_output_field("planned_value", description="计划价值PV")
    builder.add_output_field("earned_value", description="挣值EV")
    builder.add_output_field("actual_cost", description="实际成本AC")
    builder.add_output_field("schedule_variance", description="进度偏差SV")
    builder.add_output_field("cost_variance", description="成本偏差CV")
    builder.add_output_field("spi", description="进度绩效指数")
    builder.add_output_field("cpi", description="成本绩效指数")
    builder.add_output_field("eac", description="完工估算EAC")
    builder.add_output_field("alerts", description="预警信息")
    builder.add_permission("cost", "read")
    builder.add_permission("project", "read")
    return builder.build()


def get_cost_accounting_manifest() -> SkillManifest:
    """获取成本核算Skill Manifest."""
    builder = SkillManifestBuilder()
    builder.set_name("cost_accounting", "成本核算")
    builder.set_description(
        "项目成本核算与报表生成，包括直接成本、间接成本分类及利润计算。"
        "用户可以输入'成本核算'、'结算'、'成本报表'、'核算报告'等触发。"
    )
    builder.set_domain("cost")
    builder.add_input_param(
        "project_id",
        type="string",
        description="项目ID",
        required=True,
    )
    builder.add_input_param(
        "period_start",
        type="string",
        description="核算开始日期",
        required=False,
    )
    builder.add_input_param(
        "period_end",
        type="string",
        description="核算结束日期",
        required=False,
    )
    builder.add_output_field("total_direct_costs", description="直接成本合计")
    builder.add_output_field("total_indirect_costs", description="间接成本合计")
    builder.add_output_field("total_costs", description="总成本")
    builder.add_output_field("revenue", description="收入")
    builder.add_output_field("profit", description="利润")
    builder.add_output_field("profitability_ratio", description="利润率")
    builder.add_permission("cost", "read")
    builder.add_permission("project", "read")
    builder.set_async_support(True)
    return builder.build()


# ==================== 全局Manifest注册 ====================

DEFAULT_SKILL_MANIFESTS: Dict[str, SkillManifest] = {
    "project_overview": get_project_overview_manifest(),
    "weekly_report": get_weekly_report_manifest(),
    "wbs_generation": get_wbs_generation_manifest(),
    "task_update": get_task_update_manifest(),
    "risk_alert": get_risk_alert_manifest(),
    "cost_monitor": get_cost_monitor_manifest(),
    "policy_qa": get_policy_qa_manifest(),
    "project_query": get_project_query_manifest(),
    "meeting_minutes": get_meeting_minutes_manifest(),
    "compliance_review": get_compliance_review_manifest(),
    # 成本相关Skill
    "cost_estimation": get_cost_estimation_manifest(),
    "cost_monitoring": get_cost_monitoring_manifest(),
    "cost_accounting": get_cost_accounting_manifest(),
}