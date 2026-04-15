"""
PM Digital Employee - LLM Usage Log Model
LLM usage audit and statistics model.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class LLMUsageLog(Base):
    """
    LLM usage log table.

    Records every LLM API call for auditing and cost tracking.
    Logs are append-only, never modified or deleted.

    Attributes:
        id: Primary key
        trace_id: Request trace ID
        user_id: User ID
        model: Model name
        provider: LLM provider (openai/azure/zhipu/qwen)
        prompt_tokens: Input token count
        completion_tokens: Output token count
        total_tokens: Total token count
        latency_ms: Request latency in milliseconds
        skill_name: Skill that triggered the call
        success: Whether the call succeeded
        error_message: Error details if failed
        created_at: Record timestamp
    """

    __tablename__ = "llm_usage_logs"
    __table_args__ = (
        Index("ix_llm_usage_trace_id", "trace_id"),
        Index("ix_llm_usage_model", "model"),
        Index("ix_llm_usage_provider", "provider"),
        Index("ix_llm_usage_created_at", "created_at"),
        Index("ix_llm_usage_user_date", "user_id", "created_at"),
        {"comment": "LLM usage audit log"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Primary key",
    )

    trace_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Request trace ID",
    )

    user_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="User ID",
    )

    model: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Model name",
    )

    provider: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="LLM provider (openai/azure/zhipu/qwen)",
    )

    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Input token count",
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Output token count",
    )

    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total token count",
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Request latency in milliseconds",
    )

    skill_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Skill name that triggered the call",
    )

    success: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="Whether the call succeeded",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
        comment="Error details if failed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Record timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"<LLMUsageLog(id={self.id}, model={self.model}, "
            f"tokens={self.total_tokens}, success={self.success})>"
        )
