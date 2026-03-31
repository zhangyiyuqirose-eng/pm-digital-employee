"""
PM Digital Employee - Exceptions
项目经理数字员工系统 - 异常定义
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """错误码枚举."""

    # 通用错误
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    NOT_FOUND = "NOT_FOUND"

    # 认证授权错误
    UNAUTHORIZED = "UNAUTHORIZED"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # 飞书相关
    LARK_SIGNATURE_INVALID = "LARK_SIGNATURE_INVALID"
    LARK_IDEMPOTENT_CHECK_FAILED = "LARK_IDEMPOTENT_CHECK_FAILED"

    # Skill相关
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_EXECUTION_ERROR = "SKILL_EXECUTION_ERROR"

    # LLM相关
    LLM_ERROR = "LLM_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"

    # RAG相关
    RAG_NO_ANSWER = "RAG_NO_ANSWER"

    # Agent相关
    AGENT_ERROR = "AGENT_ERROR"
    TASK_TIMEOUT = "TASK_TIMEOUT"


class PMError(Exception):
    """基础异常类."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            },
        }


class SkillNotFoundError(PMError):
    """Skill未找到异常."""

    def __init__(self, skill_name: str) -> None:
        super().__init__(
            message=f"Skill not found: {skill_name}",
            code=ErrorCode.SKILL_NOT_FOUND,
            details={"skill_name": skill_name},
        )


class PermissionDeniedError(PMError):
    """权限拒绝异常."""

    def __init__(
        self,
        message: str = "Permission denied",
        resource: Optional[str] = None,
        action: Optional[str] = None,
    ) -> None:
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
            details=details,
        )


class LarkSignatureError(PMError):
    """飞书签名验证异常."""

    def __init__(self, message: str = "Invalid Lark signature") -> None:
        super().__init__(
            message=message,
            code=ErrorCode.LARK_SIGNATURE_INVALID,
        )


class LLMError(PMError):
    """LLM调用异常."""

    def __init__(
        self,
        message: str = "LLM error",
        provider: Optional[str] = None,
    ) -> None:
        details = {}
        if provider:
            details["provider"] = provider
        super().__init__(
            message=message,
            code=ErrorCode.LLM_ERROR,
            details=details,
        )


class SkillExecutionError(PMError):
    """Skill执行异常."""

    def __init__(
        self,
        skill_name: str,
        message: str = "Skill execution error",
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.SKILL_EXECUTION_ERROR,
            details={"skill_name": skill_name},
        )


class LarkError(PMError):
    """飞书相关异常."""

    def __init__(
        self,
        message: str = "Lark error",
        code: ErrorCode = ErrorCode.LARK_SIGNATURE_INVALID,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
        )


class PermissionError(PMError):
    """权限异常."""

    def __init__(
        self,
        message: str = "Permission error",
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.PERMISSION_DENIED,
        )


class ProjectAccessDeniedError(PMError):
    """项目访问拒绝异常."""

    def __init__(
        self,
        project_id: str = "",
        user_id: str = "",
    ) -> None:
        super().__init__(
            message=f"Access denied to project {project_id}",
            code=ErrorCode.PERMISSION_DENIED,
            details={"project_id": project_id, "user_id": user_id},
        )


class SkillAccessDeniedError(PMError):
    """Skill访问拒绝异常."""

    def __init__(
        self,
        skill_name: str = "",
    ) -> None:
        super().__init__(
            message=f"Access denied to skill {skill_name}",
            code=ErrorCode.PERMISSION_DENIED,
            details={"skill_name": skill_name},
        )