"""
PM Digital Employee - Approval Workflow Model
项目经理数字员工系统 - 审批流程实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base, ProjectScopedMixin
from app.domain.enums import ApprovalStatus, ApprovalType


class ApprovalWorkflow(Base, ProjectScopedMixin):
    """
    审批流程实体.

    存储审批流程实例信息。

    Attributes:
        id: 审批ID
        project_id: 所属项目ID
        type: 审批类型
        status: 审批状态
        title: 审批标题
        content: 审批内容
        applicant_id: 申请人ID
        current_approver_id: 当前审批人ID
    """

    __tablename__ = "approval_workflows"
    __table_args__ = (
        Index("ix_approval_workflows_project_id", "project_id"),
        Index("ix_approval_workflows_status", "status"),
        Index("ix_approval_workflows_type", "type"),
        Index("ix_approval_workflows_applicant_id", "applicant_id"),
        Index("ix_approval_workflows_current_approver_id", "current_approver_id"),
        {"comment": "审批流程表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="审批ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 审批信息
    type: Mapped[ApprovalType] = mapped_column(
        String(32),
        nullable=False,
        comment="审批类型",
    )

    status: Mapped[ApprovalStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ApprovalStatus.PENDING,
        comment="审批状态",
    )

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="审批标题",
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="审批内容（JSON）",
    )

    # 申请人
    applicant_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="申请人飞书用户ID",
    )

    applicant_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="申请人姓名",
    )

    # 当前审批人
    current_approver_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="当前审批人飞书用户ID",
    )

    current_approver_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="当前审批人姓名",
    )

    # 审批结果
    result: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="审批结果",
    )

    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="审批意见",
    )

    # 关联文档
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="关联文档ID",
    )

    # 时间
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="提交时间",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflow(id={self.id}, type={self.type}, status={self.status})>"