"""
PM Digital Employee - Document Model
项目经理数字员工系统 - 项目文档实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import ProjectScopedMixin
from app.domain.enums import DocumentStatus, DocumentType

if TYPE_CHECKING:
    from app.domain.models.project import Project


class ProjectDocument(ProjectScopedMixin):
    """
    项目文档实体.

    存储项目文档信息和元数据。

    Attributes:
        id: 文档ID
        project_id: 所属项目ID
        name: 文档名称
        type: 文档类型
        status: 文档状态
        file_path: 文件路径
        file_size: 文件大小
        file_type: 文件格式
        version: 版本号
        content: 文档内容（文本）
    """

    __tablename__ = "project_documents"
    __table_args__ = (
        Index("ix_project_documents_project_id", "project_id"),
        Index("ix_project_documents_type", "type"),
        Index("ix_project_documents_status", "status"),
        Index("ix_project_documents_project_type", "project_id", "type"),
        {"comment": "项目文档表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="文档ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="文档名称",
    )

    type: Mapped[DocumentType] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentType.OTHER,
        comment="文档类型",
    )

    status: Mapped[DocumentStatus] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentStatus.DRAFT,
        comment="文档状态",
    )

    # 文件信息
    file_path: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="文件路径",
    )

    file_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="文件URL",
    )

    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小（字节）",
    )

    file_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="文件格式",
    )

    # 版本信息
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="版本号",
    )

    # 文档内容（用于AI处理）
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档内容（文本）",
    )

    # 摘要
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档摘要",
    )

    # 作者
    author_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="作者飞书用户ID",
    )

    author_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="作者姓名",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        return f"<ProjectDocument(id={self.id}, name={self.name}, type={self.type})>"