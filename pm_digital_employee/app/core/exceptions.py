"""
PM Digital Employee - Unified Exception Module
项目经理数字员工系统 - 统一异常处理模块

定义统一的异常类、错误码、错误消息，
确保所有异常可追踪、可审计、用户友好。

设计原则：
- 所有业务异常必须继承PMError基类
- 所有异常必须包含错误码、错误消息、trace_id
- 错误信息不得泄露系统敏感信息
- 支持国际化错误消息
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(Enum):
    """错误码枚举.

    错误码命名规范：
    - 前缀表示错误类型
    - 数字表示具体错误
    - 1000-1999: 系统级错误
    - 2000-2999: 权限/认证错误
    - 3000-3999: 业务逻辑错误
    - 4000-4999: 数据错误
    - 5000-5999: 第三方系统错误
    """

    # 系统级错误 (1000-1999)
    INTERNAL_ERROR = ("E1001", "系统内部错误，请稍后重试")
    SERVICE_UNAVAILABLE = ("E1002", "服务暂时不可用")
    CONFIGURATION_ERROR = ("E1003", "系统配置错误")
    RATE_LIMIT_EXCEEDED = ("E1004", "请求频率超过限制，请稍后重试")
    TIMEOUT_ERROR = ("E1005", "请求处理超时")
    RESOURCE_NOT_FOUND = ("E1006", "请求的资源不存在")

    # 权限/认证错误 (2000-2999)
    UNAUTHORIZED = ("E2001", "未授权访问，请先登录")
    FORBIDDEN = ("E2002", "权限不足，拒绝访问")
    INVALID_TOKEN = ("E2003", "认证令牌无效或已过期")
    INVALID_SIGNATURE = ("E2004", "请求签名验证失败")
    PROJECT_ACCESS_DENIED = ("E2005", "无该项目访问权限")
    SKILL_ACCESS_DENIED = ("E2006", "无该技能执行权限")
    GROUP_NOT_BOUND = ("E2007", "当前群未绑定项目")
    ROLE_NOT_ALLOWED = ("E2008", "当前角色不允许执行此操作")
    CROSS_PROJECT_ACCESS = ("E2009", "禁止跨项目数据访问")

    # 业务逻辑错误 (3000-3999)
    SKILL_NOT_FOUND = ("E3001", "未找到匹配的技能")
    SKILL_DISABLED = ("E3002", "该技能未启用")
    INTENT_NOT_RECOGNIZED = ("E3003", "无法识别您的指令")
    PARAM_MISSING = ("E3004", "缺少必要参数")
    PARAM_INVALID = ("E3005", "参数格式不正确")
    DIALOG_TIMEOUT = ("E3006", "对话已超时，请重新开始")
    TASK_ALREADY_EXISTS = ("E3007", "任务已存在")
    INVALID_OPERATION = ("E3008", "无效的操作")
    BUSINESS_RULE_VIOLATION = ("E3009", "违反业务规则")

    # 数据错误 (4000-4999)
    DATA_NOT_FOUND = ("E4001", "数据不存在")
    DATA_ALREADY_EXISTS = ("E4002", "数据已存在")
    DATA_VALIDATION_ERROR = ("E4003", "数据校验失败")
    DATABASE_ERROR = ("E4004", "数据库操作错误")
    CACHE_ERROR = ("E4005", "缓存操作错误")
    VECTOR_SEARCH_ERROR = ("E4006", "向量检索错误")
    EMBEDDING_ERROR = ("E4007", "文本向量化错误")

    # 第三方系统错误 (5000-5999)
    LARK_API_ERROR = ("E5001", "飞书接口调用失败")
    LARK_MESSAGE_SEND_ERROR = ("E5002", "飞书消息发送失败")
    LARK_EVENT_ERROR = ("E5003", "飞书事件处理错误")
    LLM_API_ERROR = ("E5004", "大模型接口调用失败")
    LLM_RESPONSE_ERROR = ("E5005", "大模型响应解析失败")
    EXTERNAL_SYSTEM_ERROR = ("E5006", "外部系统调用失败")
    PROJECT_SYSTEM_ERROR = ("E5007", "项目管理系统接口错误")
    FINANCE_SYSTEM_ERROR = ("E5008", "财务系统接口错误")

    # 安全相关错误 (6000-6999)
    SECURITY_INPUT_INVALID = ("E6001", "输入内容不合法")
    SECURITY_PROMPT_INJECTION = ("E6002", "检测到潜在的安全风险")
    SECURITY_SENSITIVE_CONTENT = ("E6003", "内容包含敏感信息")
    SECURITY_COMPLIANCE_VIOLATION = ("E6004", "内容不符合合规要求")
    SECURITY_UNAUTHORIZED_ACCESS = ("E6005", "未授权访问敏感资源")

    # RAG相关错误 (7000-7999)
    RAG_NO_KNOWLEDGE_FOUND = ("E7001", "未检索到足够的制度依据")
    RAG_PERMISSION_DENIED = ("E7002", "无权限访问相关知识")
    RAG_CONTENT_PARSE_ERROR = ("E7003", "知识内容解析失败")
    RAG_INDEX_ERROR = ("E7004", "知识库索引错误")

    @property
    def code(self) -> str:
        """获取错误码."""
        return self.value[0]

    @property
    def message(self) -> str:
        """获取错误消息."""
        return self.value[1]


class PMError(Exception):
    """
    项目经理数字员工系统异常基类.

    所有业务异常必须继承此基类，
    确保异常信息统一、可追踪。

    Attributes:
        error_code: 错误码枚举
        message: 错误消息
        trace_id: 追踪ID
        details: 详细信息字典
        cause: 原始异常
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        初始化异常实例.

        Args:
            error_code: 错误码枚举
            message: 自定义错误消息，默认使用错误码对应消息
            trace_id: 追踪ID
            details: 详细信息字典（不包含敏感信息）
            cause: 原始异常
        """
        self.error_code = error_code
        self.message = message or error_code.message
        self.trace_id = trace_id
        self.details = details or {}
        self.cause = cause

        # 构建完整异常消息
        full_message = f"[{error_code.code}] {self.message}"
        if trace_id:
            full_message = f"{full_message} (trace_id: {trace_id})"

        super().__init__(full_message)

    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式（用于API响应）.

        Returns:
            Dict[str, Any]: 异常信息字典
        """
        result: Dict[str, Any] = {
            "success": False,
            "error_code": self.error_code.code,
            "error_message": self.message,
        }

        if self.trace_id:
            result["trace_id"] = self.trace_id

        # 仅在开发环境返回详细信息
        if self.details and not hasattr(self, "_hide_details"):
            # 过滤敏感信息
            safe_details = self._sanitize_details(self.details)
            result["details"] = safe_details

        return result

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤详细信息中的敏感内容.

        Args:
            details: 原始详细信息字典

        Returns:
            Dict[str, Any]: 过滤后的详细信息字典
        """
        sensitive_keys = [
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "api_key",
            "app_secret",
        ]

        safe_details = {}
        for key, value in details.items():
            if any(sk in key.lower() for sk in sensitive_keys):
                safe_details[key] = "[FILTERED]"
            elif isinstance(value, str) and len(value) > 100:
                safe_details[key] = value[:100] + "..."
            else:
                safe_details[key] = value

        return safe_details


class SystemError(PMError):
    """系统级异常."""

    def __init__(
        self,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=message,
            trace_id=trace_id,
            details=details,
            cause=cause,
        )
        # 生产环境隐藏详细错误信息
        self._hide_details = True


class AuthError(PMError):
    """认证/授权异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.UNAUTHORIZED,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
        )


class PermissionError(PMError):
    """权限异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.FORBIDDEN,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
        )


class ProjectAccessDeniedError(PermissionError):
    """项目访问权限被拒绝异常."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if project_id:
            details["project_id"] = project_id
        if user_id:
            details["user_id"] = user_id

        super().__init__(
            error_code=ErrorCode.PROJECT_ACCESS_DENIED,
            trace_id=trace_id,
            details=details,
        )


class SkillAccessDeniedError(PermissionError):
    """技能执行权限被拒绝异常."""

    def __init__(
        self,
        skill_name: Optional[str] = None,
        reason: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if skill_name:
            details["skill_name"] = skill_name
        if reason:
            details["reason"] = reason

        super().__init__(
            error_code=ErrorCode.SKILL_ACCESS_DENIED,
            trace_id=trace_id,
            details=details,
        )


class GroupNotBoundError(PermissionError):
    """飞书群未绑定项目异常."""

    def __init__(
        self,
        chat_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if chat_id:
            details["chat_id"] = chat_id

        super().__init__(
            error_code=ErrorCode.GROUP_NOT_BOUND,
            trace_id=trace_id,
            details=details,
        )


class SkillNotFoundError(PMError):
    """技能不存在异常."""

    def __init__(
        self,
        skill_name: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if skill_name:
            details["skill_name"] = skill_name

        super().__init__(
            error_code=ErrorCode.SKILL_NOT_FOUND,
            trace_id=trace_id,
            details=details,
        )


class IntentNotRecognizedError(PMError):
    """意图识别失败异常."""

    def __init__(
        self,
        user_input: Optional[str] = None,
        confidence: Optional[float] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if user_input:
            # 截断过长输入
            details["user_input"] = user_input[:100] if len(user_input) > 100 else user_input
        if confidence is not None:
            details["confidence"] = confidence

        super().__init__(
            error_code=ErrorCode.INTENT_NOT_RECOGNIZED,
            trace_id=trace_id,
            details=details,
        )


class ValidationError(PMError):
    """数据校验异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.PARAM_INVALID,
        message: Optional[str] = None,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if field_name:
            details["field"] = field_name
        if field_value is not None:
            # 隐藏敏感字段值
            if field_name and any(sk in field_name.lower() for sk in ["password", "secret", "key"]):
                details["value"] = "[FILTERED]"
            else:
                details["value"] = str(field_value)[:50]

        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
        )


class LarkError(PMError):
    """飞书接口异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.LARK_API_ERROR,
        message: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        response_code: Optional[int] = None,
        trace_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        details = {}
        if api_endpoint:
            details["api_endpoint"] = api_endpoint
        if response_code:
            details["response_code"] = response_code

        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
            cause=cause,
        )


class LLMError(PMError):
    """大模型接口异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.LLM_API_ERROR,
        message: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_length: Optional[int] = None,
        trace_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        details = {}
        if model_name:
            details["model"] = model_name
        if prompt_length:
            details["prompt_length"] = prompt_length

        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
            cause=cause,
        )


class RAGError(PMError):
    """RAG检索异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.RAG_NO_KNOWLEDGE_FOUND,
        message: Optional[str] = None,
        query: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if query:
            details["query"] = query[:100] if len(query) > 100 else query

        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
        )


class SecurityError(PMError):
    """安全相关异常."""

    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.SECURITY_INPUT_INVALID,
        message: Optional[str] = None,
        violation_type: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if violation_type:
            details["violation_type"] = violation_type

        super().__init__(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details,
        )
        # 安全错误隐藏详细信息
        self._hide_details = True


class DataNotFoundError(PMError):
    """数据不存在异常."""

    def __init__(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            error_code=ErrorCode.DATA_NOT_FOUND,
            trace_id=trace_id,
            details=details,
        )


class DatabaseError(PMError):
    """数据库操作异常."""

    def __init__(
        self,
        message: Optional[str] = None,
        operation: Optional[str] = None,
        trace_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            trace_id=trace_id,
            details=details,
            cause=cause,
        )
        # 数据库错误隐藏详细信息
        self._hide_details = True