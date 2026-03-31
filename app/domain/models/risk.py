"""
PM Digital Employee - Risk Model
项目经理数字员工系统 - 风险实体模型
"""

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import ProjectScopedMixin
from app.domain.enums import RiskCategory, RiskLevel, RiskStatus

if TYPE_CHECKING:
    from app.domain.models.project import Project


class ProjectRisk(ProjectScopedMixin):
    """
    项目风险实体.

    存储项目风险信息和处置状态。

    Attributes:
        id: 风险ID
        project_id: 所属项目ID
        title: 风险标题
        description: 风险描述
        category: 风险类别
        level: 风险等级
        status: 风险状态
        probability: 发生概率（1-5）
        impact: 影响程度（1-5）
        identified_date: 识别日期
        due_date: 预计解决日期
        mitigation_plan: 缓解措施
        owner_id: 风险负责人ID
    """

    __tablename__ = "project_risks"
    __table_args__ = (
        Index("ix_project_risks_project_id", "project_id"),
        Index("ix_project_risks_level", "level"),
        Index("ix_project_risks_status", "status"),
        Index("ix_project_risks_category", "category"),
        Index("ix_project_risks_project_level", "project_id", "level"),
        {"comment": "项目风险表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="风险ID",
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
    code: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="风险编码",
    )

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="风险标题",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="风险描述",
    )

    # 风险属性
    category: Mapped[RiskCategory] = mapped_column(
        String(32),
        nullable=False,
        comment="风险类别",
    )

    level: Mapped[RiskLevel] = mapped_column(
        String(32),
        nullable=False,
        default=RiskLevel.MEDIUM,
        comment="风险等级",
    )

    status: Mapped[RiskStatus] = mapped_column(
        String(32),
        nullable=False,
        default=RiskStatus.IDENTIFIED,
        comment="风险状态",
    )

    # 风险评估
    probability: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="发生概率（1-5）",
    )

    impact: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="影响程度（1-5）",
    )

    # 时间信息
    identified_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="识别日期",
    )

    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="预计解决日期",
    )

    resolved_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="实际解决日期",
    )

    # 缓解措施
    mitigation_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="缓解措施",
    )

    mitigation_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="缓解措施状态",
    )

    # 负责人
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="风险负责人飞书用户ID",
    )

    owner_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="风险负责人姓名",
    )

    # 根因分析
    root_cause: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="根因分析",
    )

    # AI生成的建议
    ai_suggestion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI生成的应对建议",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="risks",
    )

    def __repr__(self) -> str:
        return f"<ProjectRisk(id={self.id}, title={self.title}, level={self.level})>"

    @property
    def risk_score(self) -> int:
        """计算风险评分（概率×影响）."""
        return self.probability * self.impact

    @property
    def is_high_risk(self) -> bool:
        """判断是否高风险."""
        return self.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]