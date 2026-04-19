"""
PM Digital Employee - WBS Version Model
项目经理数字员工系统 - WBS版本管理实体模型

v1.2.0新增：支持多源数据录入，WBS版本管理和历史回滚
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, ProjectScopedMixin
from app.domain.enums import DataSource, WBSStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class WBSVersion(Base, ProjectScopedMixin):
    """
    WBS版本管理实体.
    
    存储WBS版本信息，支持版本历史记录和回滚。
    WBS分解结果自动同步至任务管理模块。

    Attributes:
        id: WBS版本唯一标识
        project_id: 所属项目ID
        version_number: 版本号
        version_name: 版本名称
        description: 版本描述
        wbs_data: WBS树形结构（JSON）
        status: WBS状态
        is_published: 是否已发布
        is_current: 是否当前版本
        created_by_id: 创建者飞书用户ID
        created_by_name: 创建者姓名
        published_at: 发布时间
        published_by_id: 发布者飞书用户ID
        published_by_name: 发布者姓名
        data_source: 数据来源
    """

    __tablename__ = "wbs_versions"
    __table_args__ = (
        Index("ix_wbs_versions_project_id", "project_id"),
        Index("ix_wbs_versions_version_number", "version_number"),
        Index("ix_wbs_versions_is_current", "is_current"),
        Index("ix_wbs_versions_data_source", "data_source"),
        {"comment": "WBS版本管理表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="WBS版本ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 版本信息
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="版本号",
    )

    version_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="版本名称",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="版本描述",
    )

    # WBS内容（树形结构JSON）
    wbs_data: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="WBS树形结构（JSON）",
    )

    # 状态
    status: Mapped[WBSStatus] = mapped_column(
        String(32),
        nullable=False,
        default=WBSStatus.DRAFT,
        comment="WBS状态",
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已发布",
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否当前版本",
    )

    # 创建者信息
    created_by_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="创建者飞书用户ID",
    )

    created_by_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="创建者姓名",
    )

    # 发布信息
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="发布时间",
    )

    published_by_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="发布者飞书用户ID",
    )

    published_by_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="发布者姓名",
    )

    # 数据来源
    data_source: Mapped[DataSource] = mapped_column(
        String(32),
        nullable=False,
        default=DataSource.LARK_CARD,
        comment="数据来源",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="wbs_versions",
    )

    def __repr__(self) -> str:
        return f"<WBSVersion(id={self.id}, version={self.version_number}, status={self.status})>"