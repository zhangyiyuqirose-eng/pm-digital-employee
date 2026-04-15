"""
PM Digital Employee - Orchestrator Schemas
项目经理数字员工系统 - 编排层Pydantic模型

定义编排引擎的核心数据结构：意图识别结果、Skill执行上下文、对话状态等。
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """意图类型."""

    SKILL_EXECUTION = "skill_execution"  # Skill执行意图
    CLARIFICATION = "clarification"  # 澄清意图（置信度不足）
    AMBIGUOUS = "ambiguous"  # 模糊意图（多个候选）
    UNKNOWN = "unknown"  # 未知意图
    REJECTION = "rejection"  # 拒绝执行（安全防护）


class IntentResult(BaseModel):
    """意图识别结果."""

    intent_type: IntentType = Field(..., description="意图类型")
    matched_skill: Optional[str] = Field(None, description="匹配的Skill名称")
    skill_description: Optional[str] = Field(None, description="Skill描述")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    candidate_skills: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="候选Skill列表",
    )
    extracted_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="提取的参数",
    )
    missing_params: List[str] = Field(
        default_factory=list,
        description="缺失的必填参数",
    )
    rejection_reason: Optional[str] = Field(None, description="拒绝原因")
    raw_response: Optional[str] = Field(None, description="LLM原始响应")
    tokens_used: int = Field(0, description="消耗的Token数")


class SkillExecutionContext(BaseModel):
    """Skill执行上下文."""

    trace_id: str = Field(..., description="追踪ID")
    user_id: str = Field(..., description="用户飞书ID")
    chat_id: str = Field(..., description="会话ID")
    chat_type: str = Field("p2p", description="会话类型: p2p/group")
    project_id: Optional[uuid.UUID] = Field(None, description="项目ID")
    user_role: Optional[str] = Field(None, description="用户角色")
    skill_name: str = Field(..., description="Skill名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="对话历史",
    )
    message_id: Optional[str] = Field(None, description="飞书消息ID")
    parent_message_id: Optional[str] = Field(None, description="父消息ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class SkillExecutionResult(BaseModel):
    """Skill执行结果."""

    success: bool = Field(..., description="是否成功")
    skill_name: str = Field(..., description="Skill名称")
    output: Optional[Dict[str, Any]] = Field(None, description="输出结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    requires_confirmation: bool = Field(
        False,
        description="是否需要用户确认",
    )
    confirmation_card: Optional[Dict[str, Any]] = Field(
        None,
        description="确认卡片",
    )
    is_async: bool = Field(False, description="是否异步任务")
    async_task_id: Optional[str] = Field(None, description="异步任务ID")
    presentation_type: str = Field(
        "text",
        description="展示类型: text/card/file",
    )
    presentation_data: Optional[Dict[str, Any]] = Field(
        None,
        description="展示数据",
    )
    duration_ms: int = Field(0, description="耗时毫秒")
    tokens_input: int = Field(0, description="LLM输入Token")
    tokens_output: int = Field(0, description="LLM输出Token")


class DialogState(str, Enum):
    """对话状态."""

    IDLE = "idle"  # 空闲状态
    INTENT_RECOGNIZED = "intent_recognized"  # 意图已识别
    PARAM_COLLECTING = "param_collecting"  # 参数收集中
    CONFIRMATION_PENDING = "confirmation_pending"  # 等待确认
    EXECUTING = "executing"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class DialogSession(BaseModel):
    """多轮对话会话."""

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="会话ID",
    )
    user_id: str = Field(..., description="用户ID")
    chat_id: str = Field(..., description="会话ID")
    project_id: Optional[uuid.UUID] = Field(None, description="项目ID")
    state: DialogState = Field(DialogState.IDLE, description="当前状态")
    current_skill: Optional[str] = Field(None, description="当前Skill")
    collected_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="已收集参数",
    )
    missing_params: List[str] = Field(
        default_factory=list,
        description="缺失参数",
    )
    intent_result: Optional[IntentResult] = Field(None, description="意图识别结果")
    execution_result: Optional[SkillExecutionResult] = Field(
        None,
        description="执行结果",
    )
    conversation_messages: List[Dict[str, str]] = Field(
        default_factory=list,
        description="对话消息列表",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="更新时间",
    )
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class IntentRecognitionRequest(BaseModel):
    """意图识别请求."""

    user_message: str = Field(..., description="用户消息内容")
    user_id: str = Field(..., description="用户ID")
    chat_id: str = Field(..., description="会话ID")
    chat_type: str = Field("p2p", description="会话类型")
    project_id: Optional[uuid.UUID] = Field(None, description="项目ID")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="对话历史",
    )
    available_skills: List[str] = Field(
        default_factory=list,
        description="可用Skill列表",
    )


class SkillManifest(BaseModel):
    """Skill Manifest规范."""

    skill_name: str = Field(..., description="Skill唯一标识")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="功能描述（用于意图识别）")
    version: str = Field("1.0.0", description="版本号")
    domain: str = Field("general", description="所属业务域")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输入参数Schema",
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="输出结果Schema",
    )
    allowed_roles: List[str] = Field(
        default_factory=lambda: ["project_manager", "pm", "tech_lead", "member"],
        description="允许的角色列表",
    )
    required_permissions: List[Dict[str, str]] = Field(
        default_factory=list,
        description="所需权限",
    )
    enabled_by_default: bool = Field(True, description="默认启用")
    supports_async: bool = Field(False, description="支持异步执行")
    supports_confirmation: bool = Field(False, description="需要确认")
    dependencies: List[str] = Field(default_factory=list, description="依赖Skill")


class UserContext(BaseModel):
    """用户上下文."""

    user_id: str = Field(..., description="用户飞书ID")
    user_name: Optional[str] = Field(None, description="用户姓名")
    user_role: Optional[str] = Field(None, description="用户角色")
    department_id: Optional[str] = Field(None, description="部门ID")
    accessible_projects: List[uuid.UUID] = Field(
        default_factory=list,
        description="可访问的项目列表",
    )
    current_project: Optional[uuid.UUID] = Field(None, description="当前项目")
    chat_type: str = Field("p2p", description="会话类型")
    chat_id: str = Field(..., description="会话ID")
    is_group_chat: bool = Field(False, description="是否群聊")
    group_bound_project: Optional[uuid.UUID] = Field(
        None,
        description="群绑定的项目",
    )


class MessagePayload(BaseModel):
    """消息载荷."""

    message_id: str = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容")
    content_type: str = Field("text", description="内容类型")
    sender_open_id: str = Field(..., description="发送者OpenID")
    chat_id: str = Field(..., description="会话ID")
    chat_type: str = Field("p2p", description="会话类型")
    mentions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="@列表",
    )
    parent_id: Optional[str] = Field(None, description="父消息ID")
    root_id: Optional[str] = Field(None, description="根消息ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")


class ClarificationCardData(BaseModel):
    """澄清卡片数据."""

    matched_skill: str = Field(..., description="匹配的Skill")
    skill_description: str = Field(..., description="Skill描述")
    confidence: float = Field(..., description="置信度")
    alternative_skills: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="备选Skill",
    )


class ParamCollectionPrompt(BaseModel):
    """参数收集提示."""

    missing_param: str = Field(..., description="缺失的参数名")
    param_description: str = Field(..., description="参数描述")
    param_type: str = Field("string", description="参数类型")
    examples: List[str] = Field(default_factory=list, description="示例值")
    prompt_message: str = Field(..., description="提示消息")