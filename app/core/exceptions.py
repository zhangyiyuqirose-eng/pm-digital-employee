"""
PM Digital Employee - Exceptions
PM Digital Employee System - Exception definitions

Lark as the primary user interaction entrypoint.
"""

import traceback
import logging
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class ErrorCode(Enum):
    """错误码枚举"""
    # 通用错误
    SYSTEM_ERROR = (500000, "系统内部错误")
    PARAMETER_ERROR = (400000, "参数错误")
    AUTHENTICATION_FAILED = (401000, "认证失败")
    PERMISSION_DENIED = (403000, "权限不足")
    RESOURCE_NOT_FOUND = (404000, "资源不存在")
    REQUEST_LIMIT_EXCEEDED = (429000, "请求频率超限")

    # 业务错误
    PROJECT_NOT_FOUND = (600001, "项目不存在")
    USER_NOT_FOUND = (600002, "用户不存在")
    SKILL_EXECUTION_FAILED = (600003, "技能执行失败")
    INVALID_DIALOG_STATE = (600004, "无效对话状态")

    # Lark相关
    LARK_SIGNATURE_INVALID = (700001, "飞书签名验证失败")
    LARK_IDEMPOTENT_CHECK_FAILED = (700002, "飞书幂等性检查失败")
    LARK_API_ERROR = (700003, "飞书API调用错误")
    LARK_DECRYPT_ERROR = (700004, "飞书消息解密错误")

    # AI/LLM相关
    LLM_ERROR = (800001, "AI服务错误")
    LLM_TIMEOUT = (800002, "AI服务超时")
    LLM_RATE_LIMITED = (800003, "AI服务调用频率限制")

    # RAG相关
    RAG_NO_ANSWER = (800004, "知识库检索无结果")
    RAG_RETRIEVAL_ERROR = (800005, "知识库检索错误")

    # Skill相关
    SKILL_NOT_FOUND = (900001, "技能未找到")
    SKILL_EXECUTION_ERROR = (900002, "技能执行错误")

    # Agent相关
    AGENT_ERROR = (900003, "智能代理错误")
    TASK_TIMEOUT = (900004, "任务执行超时")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class APIException(Exception):
    """API异常基类"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message or error_code.message
        self.details = details or {}
        self.trace_id = trace_id or str(uuid.uuid4())

        # 记录异常信息
        logger = logging.getLogger(__name__)
        logger.error(
            f"API Exception: code={error_code.code}, message={self.message}, "
            f"details={self.details}, trace_id={self.trace_id}",
            exc_info=True
        )

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为API响应格式"""
        return {
            "success": False,
            "code": self.error_code.code,
            "message": self.message,
            "details": self.details,
            "trace_id": self.trace_id
        }


class ParameterValidationError(APIException):
    """参数验证异常"""
    def __init__(self, param_name: str, message: str, trace_id: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.PARAMETER_ERROR,
            message=f"参数 '{param_name}' 验证失败: {message}",
            details={"param_name": param_name, "error_message": message},
            trace_id=trace_id
        )


class AuthenticationException(APIException):
    """认证异常"""
    def __init__(self, message: str = "认证失败", trace_id: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            message=message,
            trace_id=trace_id
        )


class PermissionException(APIException):
    """权限异常"""
    def __init__(self, message: str = "权限不足", trace_id: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message,
            trace_id=trace_id
        )


class SkillNotFoundError(APIException):
    """Skill未找到异常."""

    def __init__(self, skill_name: str, trace_id: Optional[str] = None) -> None:
        super().__init__(
            error_code=ErrorCode.SKILL_NOT_FOUND,
            message=f"Skill not found: {skill_name}",
            details={"skill_name": skill_name},
            trace_id=trace_id
        )


class PermissionDeniedError(APIException):
    """权限拒绝异常."""

    def __init__(
        self,
        message: str = "Permission denied",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=message,
            details=details,
            trace_id=trace_id
        )


class LarkSignatureError(APIException):
    """飞书 signature verification exception."""

    def __init__(self, message: str = "Invalid Lark signature", trace_id: Optional[str] = None) -> None:
        super().__init__(
            error_code=ErrorCode.LARK_SIGNATURE_INVALID,
            message=message,
            trace_id=trace_id
        )


class LarkError(APIException):
    """飞书 API exception."""

    def __init__(
        self,
        message: str = "Lark error",
        code: ErrorCode = ErrorCode.LARK_API_ERROR,
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_code=code,
            message=message,
            trace_id=trace_id
        )


class LarkDecryptError(APIException):
    """飞书 decryption exception."""

    def __init__(self, message: str = "Lark decrypt error", trace_id: Optional[str] = None) -> None:
        super().__init__(
            error_code=ErrorCode.LARK_DECRYPT_ERROR,
            message=message,
            trace_id=trace_id
        )


class LLMError(APIException):
    """LLM调用异常."""

    def __init__(
        self,
        message: str = "LLM error",
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        super().__init__(
            error_code=ErrorCode.LLM_ERROR,
            message=message,
            details=details,
            trace_id=trace_id
        )


class LLMRateLimitError(APIException):
    """LLM限流异常."""

    def __init__(
        self,
        message: str = "LLM rate limited",
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        details = {"error_type": "rate_limit"}
        if provider:
            details["provider"] = provider
        super().__init__(
            error_code=ErrorCode.LLM_RATE_LIMITED,
            message=message,
            details=details,
            trace_id=trace_id
        )


class GroupNotBoundError(APIException):
    """群组未绑定项目异常."""

    def __init__(self, chat_id: str = "", trace_id: Optional[str] = None) -> None:
        super().__init__(
            error_code=ErrorCode.PROJECT_NOT_FOUND,
            message=f"Group {chat_id} is not bound to any project",
            details={"chat_id": chat_id},
            trace_id=trace_id
        )


class OrchestratorError(APIException):
    """编排器异常."""

    def __init__(
        self,
        message: str = "Orchestrator error",
        code: ErrorCode = ErrorCode.SYSTEM_ERROR,
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_code=code,
            message=message,
            trace_id=trace_id
        )


class SkillExecutionFailedError(APIException):
    """技能执行失败异常."""

    def __init__(self, message: str, skill_name: str = "", trace_id: Optional[str] = None) -> None:
        super().__init__(
            error_code=ErrorCode.SKILL_EXECUTION_FAILED,
            message=message,
            details={"skill_name": skill_name},
            trace_id=trace_id
        )


class ProjectAccessDeniedError(APIException):
    """项目访问拒绝异常."""

    def __init__(
        self,
        project_id: str = "",
        user_id: str = "",
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=f"Access denied to project {project_id}",
            details={"project_id": project_id, "user_id": user_id},
            trace_id=trace_id
        )


class SkillAccessDeniedError(APIException):
    """Skill access denied exception."""

    def __init__(
        self,
        skill_name: str = "",
        trace_id: Optional[str] = None,
    ) -> None:
        super().__init__(
            error_code=ErrorCode.PERMISSION_DENIED,
            message=f"Access denied to skill {skill_name}",
            details={"skill_name": skill_name},
            trace_id=trace_id
        )