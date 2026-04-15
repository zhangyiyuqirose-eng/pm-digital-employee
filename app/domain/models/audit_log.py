"""
PM Digital Employee - Audit Log Model
项目经理数字员工系统 - 审计日志实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, AuditMixin
from app.domain.enums import AuditAction


class AuditLog(Base, AuditMixin):
    """
    审计日志实体.

    记录所有用户操作、系统操作的审计日志。
    日志仅追加写入，不可修改、不可删除。

    Attributes:
        id: 日志ID
        trace_id: 追踪ID
        user_id: 操作用户ID
        project_id: 相关项目ID
        action: 操作类型
        resource_type: 资源类型
        resource_id: 资源ID
        result: 操作结果
        details: 详细信息（JSON）
        ip_address: 客户端IP
        user_agent: 用户代理
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_trace_id", "trace_id"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_project_id", "project_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_project_created", "project_id", "created_at"),
        {"comment": "审计日志表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="日志ID",
    )

    # 追踪ID
    trace_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="追踪ID",
    )

    # 用户信息
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="操作用户飞书ID",
    )

    user_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="用户姓名",
    )

    # 项目信息
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="相关项目ID",
    )

    # 操作信息
    action: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="操作类型",
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="资源类型",
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="资源ID",
    )

    # 结果
    result: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="success",
        comment="操作结果（success/failed）",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )

    # 详细信息
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="详细信息（JSON）",
    )

    request_params: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="请求参数（JSON）",
    )

    response_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="响应摘要",
    )

    # 客户端信息
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="客户端IP",
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="用户代理",
    )

    # 耗时
    duration_ms: Mapped[Optional[int]] = mapped_column(
        None,
        nullable=True,
        comment="耗时（毫秒）",
    )

    # Skill相关
    skill_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Skill名称",
    )

    # LLM相关
    llm_model: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="LLM模型名称",
    )

    llm_tokens_input: Mapped[Optional[int]] = mapped_column(
        None,
        nullable=True,
        comment="LLM输入Token数",
    )

    llm_tokens_output: Mapped[Optional[int]] = mapped_column(
        None,
        nullable=True,
        comment="LLM输出Token数",
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, result={self.result})>"