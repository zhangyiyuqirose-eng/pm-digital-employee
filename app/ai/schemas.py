"""
PM Digital Employee - AI Schemas
项目经理数字员工系统 - AI能力层Pydantic模型

定义LLM调用、Prompt管理、安全防护相关的数据结构。
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """LLM提供商."""

    OPENAI = "openai"
    AZURE = "azure"
    ZHIPU = "zhipu"
    QWEN = "qwen"
    LOCAL = "local"


class LLMRequest(BaseModel):
    """LLM请求."""

    prompt: str = Field(..., description="Prompt内容")
    model: str = Field(..., description="模型名称")
    max_tokens: int = Field(2000, description="最大输出Token")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="温度")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top P")
    stop_sequences: List[str] = Field(default_factory=list, description="停止序列")
    system_prompt: Optional[str] = Field(None, description="系统Prompt")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="对话历史",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class LLMResponse(BaseModel):
    """LLM响应."""

    content: str = Field(..., description="生成内容")
    model: str = Field(..., description="模型名称")
    prompt_tokens: int = Field(0, description="输入Token数")
    completion_tokens: int = Field(0, description="输出Token数")
    total_tokens: int = Field(0, description="总Token数")
    finish_reason: str = Field("stop", description="结束原因")
    latency_ms: int = Field(0, description="延迟毫秒")
    request_id: Optional[str] = Field(None, description="请求ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class ChatMessage(BaseModel):
    """聊天消息."""

    role: str = Field(..., description="角色: system/user/assistant")
    content: str = Field(..., description="内容")


class ChatRequest(BaseModel):
    """聊天请求."""

    messages: List[ChatMessage] = Field(..., description="消息列表")
    model: str = Field(..., description="模型名称")
    max_tokens: int = Field(2000, description="最大输出Token")
    temperature: float = Field(0.7, description="温度")
    stream: bool = Field(False, description="是否流式输出")


class PromptTemplate(BaseModel):
    """Prompt模板."""

    name: str = Field(..., description="模板名称")
    description: str = Field("", description="模板描述")
    template: str = Field(..., description="模板内容")
    input_variables: List[str] = Field(
        default_factory=list,
        description="输入变量列表",
    )
    version: str = Field("1.0.0", description="版本号")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class SafetyCheckResult(BaseModel):
    """安全检查结果."""

    is_safe: bool = Field(True, description="是否安全")
    is_malicious: bool = Field(False, description="是否恶意")
    risk_level: str = Field("low", description="风险等级: low/medium/high/critical")
    violations: List[str] = Field(default_factory=list, description="违规项")
    explanation: str = Field("", description="解释说明")
    original_content: str = Field("", description="原始内容")
    sanitized_content: Optional[str] = Field(None, description="净化后的内容")


class PromptInjectionCheckResult(BaseModel):
    """提示词注入检查结果."""

    is_malicious: bool = Field(False, description="是否恶意")
    risk_level: str = Field("low", description="风险等级")
    detected_patterns: List[str] = Field(
        default_factory=list,
        description="检测到的注入模式",
    )
    explanation: str = Field("", description="解释说明")


class ContentComplianceResult(BaseModel):
    """内容合规检查结果."""

    is_compliant: bool = Field(True, description="是否合规")
    violations: List[str] = Field(default_factory=list, description="违规项")
    categories: List[str] = Field(default_factory=list, description="违规类别")
    confidence: float = Field(1.0, description="置信度")
    original_content: str = Field("", description="原始内容")


class OutputValidationResult(BaseModel):
    """输出校验结果."""

    is_valid: bool = Field(True, description="是否有效")
    parsed_output: Optional[Dict[str, Any]] = Field(None, description="解析后的输出")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")


class LLMUsageRecord(BaseModel):
    """LLM使用记录."""

    trace_id: str = Field(..., description="追踪ID")
    user_id: str = Field(..., description="用户ID")
    model: str = Field(..., description="模型名称")
    prompt_tokens: int = Field(0, description="输入Token")
    completion_tokens: int = Field(0, description="输出Token")
    total_tokens: int = Field(0, description="总Token")
    latency_ms: int = Field(0, description="延迟")
    skill_name: Optional[str] = Field(None, description="Skill名称")
    success: bool = Field(True, description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
    )


class StructuredOutputSchema(BaseModel):
    """结构化输出Schema."""

    type: str = Field("object", description="类型")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="属性定义",
    )
    required: List[str] = Field(default_factory=list, description="必填字段")
    definitions: Optional[Dict[str, Any]] = Field(None, description="定义")


class TokenUsage(BaseModel):
    """Token使用统计."""

    total_input: int = Field(0, description="总输入Token")
    total_output: int = Field(0, description="总输出Token")
    total_tokens: int = Field(0, description="总Token")
    request_count: int = Field(0, description="请求数")
    period_start: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="统计周期开始",
    )
    period_end: Optional[datetime] = Field(None, description="统计周期结束")


class EmbeddingRequest(BaseModel):
    """Embedding请求."""

    input: str = Field(..., description="输入文本")
    model: str = Field("text-embedding-ada-002", description="模型名称")


class EmbeddingResponse(BaseModel):
    """Embedding响应."""

    embedding: List[float] = Field(..., description="向量")
    model: str = Field(..., description="模型名称")
    tokens: int = Field(0, description="Token数")
    latency_ms: int = Field(0, description="延迟")


class LLMConfig(BaseModel):
    """LLM配置."""

    provider: LLMProvider = Field(LLMProvider.OPENAI, description="提供商")
    model_name: str = Field("gpt-4", description="模型名称")
    api_key: str = Field("", description="API密钥")
    api_base: str = Field("", description="API地址")
    max_tokens: int = Field(2000, description="最大Token")
    temperature: float = Field(0.7, description="温度")
    timeout: int = Field(60, description="超时秒数")
    retry_count: int = Field(3, description="重试次数")
    retry_delay: float = Field(1.0, description="重试延迟")