"""
PM Digital Employee - Core Module
项目经理数字员工系统 - 核心模块初始化
"""

from app.core.config import Settings, get_settings, settings
from app.core.exceptions import (
    AuthError,
    DataNotFoundError,
    DatabaseError,
    ErrorCode,
    GroupNotBoundError,
    IntentNotRecognizedError,
    LarkError,
    LLMError,
    PMError,
    PermissionError,
    ProjectAccessDeniedError,
    RAGError,
    SecurityError,
    SkillAccessDeniedError,
    SkillNotFoundError,
    SystemError,
    ValidationError,
)
from app.core.logging import (
    LogContext,
    clear_context,
    get_logger,
    get_trace_id,
    set_project_id,
    set_trace_id,
    set_user_id,
    setup_logging,
)
from app.core.middleware import (
    AuditMiddleware,
    ExceptionHandlerMiddleware,
    RequestLoggingMiddleware,
    TraceIDMiddleware,
    setup_middlewares,
)
from app.core.security import (
    DataMasker,
    LarkSignatureVerifier,
    PasswordManager,
    SecretGenerator,
    TokenManager,
)

__all__ = [
    # Config
    "settings",
    "Settings",
    "get_settings",
    # Exceptions
    "PMError",
    "SystemError",
    "AuthError",
    "PermissionError",
    "ProjectAccessDeniedError",
    "SkillAccessDeniedError",
    "GroupNotBoundError",
    "SkillNotFoundError",
    "IntentNotRecognizedError",
    "ValidationError",
    "DataNotFoundError",
    "DatabaseError",
    "LarkError",
    "LLMError",
    "RAGError",
    "SecurityError",
    "ErrorCode",
    # Logging
    "setup_logging",
    "get_logger",
    "set_trace_id",
    "get_trace_id",
    "set_user_id",
    "set_project_id",
    "clear_context",
    "LogContext",
    # Middleware
    "setup_middlewares",
    "TraceIDMiddleware",
    "RequestLoggingMiddleware",
    "AuditMiddleware",
    "ExceptionHandlerMiddleware",
    # Security
    "PasswordManager",
    "TokenManager",
    "LarkSignatureVerifier",
    "SecretGenerator",
    "DataMasker",
]