"""
PM Digital Employee - Domain Module
项目经理数字员工系统 - 领域模型模块初始化
"""

from app.domain.base import (
    AuditMixin,
    Base,
    BaseModel,
    FeldType,
    FieldType,
    FullAuditModel,
    ProjectScopedMixin,
    ProjectScopedModel,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)

__all__ = [
    "Base",
    "BaseModel",
    "ProjectScopedModel",
    "FullAuditModel",
    "ProjectScopedMixin",
    "SoftDeleteMixin",
    "TenantMixin",
    "AuditMixin",
    "TimestampMixin",
    "FieldType",
    "FeldType",  # 兼容性导出（修复拼写错误）
]