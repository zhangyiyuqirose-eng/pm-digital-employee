"""
PM Digital Employee - Skill Definition Model
项目经理数字员工系统 - Skill定义实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class SkillDefinition(Base):
    """
    Skill定义实体.

    存储系统支持的Skill技能定义和配置。

    Attributes:
        id: Skill定义ID
        skill_name: Skill唯一标识名
        display_name: 显示名称
        description: 功能描述
        manifest: Skill清单配置（JSON）
        version: 版本号
        is_enabled: 是否启用
        enabled_by_default: 是否默认启用
    """

    __tablename__ = "skill_definitions"
    __table_args__ = (
        Index("ix_skill_definitions_skill_name", "skill_name", unique=True),
        Index("ix_skill_definitions_is_enabled", "is_enabled"),
        Index("ix_skill_definitions_domain", "domain"),
        {"comment": "Skill定义表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Skill定义ID",
    )

    # 基本信息
    skill_name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="Skill唯一标识名",
    )

    display_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="显示名称",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="功能描述",
    )

    # 配置
    manifest: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Skill清单配置（JSON）",
    )

    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        comment="版本号",
    )

    # 分类
    domain: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="general",
        comment="业务域",
    )

    # 状态
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用",
    )

    enabled_by_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否默认启用",
    )

    # 输入输出Schema
    input_schema: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="输入参数Schema（JSON）",
    )

    output_schema: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="输出结果Schema（JSON）",
    )

    # 权限配置
    allowed_roles: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="允许的角色列表（JSON）",
    )

    required_permissions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="所需权限列表（JSON）",
    )

    # 执行配置
    supports_async: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否支持异步执行",
    )

    supports_confirmation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否需要执行确认",
    )

    timeout_seconds: Mapped[int] = mapped_column(
        None,
        nullable=False,
        default=120,
        comment="执行超时时间（秒）",
    )

    def __repr__(self) -> str:
        return f"<SkillDefinition(id={self.id}, skill_name={self.skill_name})>"


class ProjectSkillSwitch(Base):
    """
    项目Skill开关实体.

    存储项目级别的Skill启用状态。

    Attributes:
        id: 开关记录ID
        project_id: 项目ID
        skill_id: Skill定义ID
        is_enabled: 是否启用
    """

    __tablename__ = "project_skill_switches"
    __table_args__ = (
        Index("ix_project_skill_switches_project_id", "project_id"),
        Index("ix_project_skill_switches_skill_id", "skill_id"),
        Index("uq_project_skill", "project_id", "skill_id", unique=True),
        {"comment": "项目Skill开关表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="开关记录ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # Skill ID
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Skill定义ID",
    )

    # 状态
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用",
    )

    enabled_by: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="启用/禁用操作人",
    )

    def __repr__(self) -> str:
        return f"<ProjectSkillSwitch(project_id={self.project_id}, skill_id={self.skill_id}, enabled={self.is_enabled})>"