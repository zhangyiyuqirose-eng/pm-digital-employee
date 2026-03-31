"""
PM Digital Employee - Cost Models
项目经理数字员工系统 - 成本实体模型（预算和实际）
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import ProjectScopedMixin
from app.domain.enums import CostCategory

if TYPE_CHECKING:
    from app.domain.models.project import Project


class ProjectCostBudget(ProjectScopedMixin):
    """
    项目成本预算实体.

    存储项目预算信息。

    Attributes:
        id: 预算记录ID
        project_id: 所属项目ID
        category: 成本类别
        amount: 预算金额
        description: 描述
        fiscal_year: 财年
    """

    __tablename__ = "project_cost_budgets"
    __table_args__ = (
        Index("ix_project_cost_budgets_project_id", "project_id"),
        Index("ix_project_cost_budgets_category", "category"),
        Index("ix_project_cost_budgets_fiscal_year", "fiscal_year"),
        {"comment": "项目成本预算表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="预算记录ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 成本类别
    category: Mapped[CostCategory] = mapped_column(
        String(32),
        nullable=False,
        comment="成本类别",
    )

    # 金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="预算金额（元）",
    )

    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )

    # 财年
    fiscal_year: Mapped[Optional[int]] = mapped_column(
        None,
        nullable=True,
        comment="财年",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="cost_budgets",
    )

    def __repr__(self) -> str:
        return f"<ProjectCostBudget(id={self.id}, category={self.category}, amount={self.amount})>"


class ProjectCostActual(ProjectScopedMixin):
    """
    项目成本实际支出实体.

    存储项目实际支出信息。

    Attributes:
        id: 支出记录ID
        project_id: 所属项目ID
        category: 成本类别
        amount: 实际金额
        expense_date: 支出日期
        description: 描述
        invoice_number: 发票号
    """

    __tablename__ = "project_cost_actuals"
    __table_args__ = (
        Index("ix_project_cost_actuals_project_id", "project_id"),
        Index("ix_project_cost_actuals_category", "category"),
        Index("ix_project_cost_actuals_expense_date", "expense_date"),
        {"comment": "项目成本实际支出表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="支出记录ID",
    )

    # 项目ID
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="项目ID",
    )

    # 成本类别
    category: Mapped[CostCategory] = mapped_column(
        String(32),
        nullable=False,
        comment="成本类别",
    )

    # 金额
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="实际金额（元）",
    )

    # 支出日期
    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="支出日期",
    )

    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )

    # 发票信息
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="发票号",
    )

    # 审批状态
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        default="pending",
        comment="审批状态",
    )

    # 关联关系
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="cost_actuals",
    )

    def __repr__(self) -> str:
        return f"<ProjectCostActual(id={self.id}, category={self.category}, amount={self.amount})>"