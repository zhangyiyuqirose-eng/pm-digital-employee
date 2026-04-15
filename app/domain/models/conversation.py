"""
PM Digital Employee - Conversation Models
项目经理数字员工系统 - 会话和消息实体模型
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base, AuditMixin, ProjectScopedMixin
from app.domain.enums import ConversationRole, DialogState

if TYPE_CHECKING:
    from app.domain.models.project import Project


class ConversationSession(Base, AuditMixin, ProjectScopedMixin):
    """
    对话会话实体.

    存储用户与机器人的对话会话信息。

    Attributes:
        id: 会话ID
        project_id: 所属项目ID
        user_id: 用户飞书ID
        chat_id: 飞书会话ID
        state: 会话状态
        matched_skill: 匹配的Skill名称
        context: 会话上下文（JSON）
    """

    __tablename__ = "conversation_sessions"
    __table_args__ = (
        Index("ix_conversation_sessions_user_id", "user_id"),
        Index("ix_conversation_sessions_chat_id", "chat_id"),
        Index("ix_conversation_sessions_project_id", "project_id"),
        Index("ix_conversation_sessions_state", "state"),
        {"comment": "对话会话表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="会话ID",
    )

    # 项目ID
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="项目ID",
    )

    # 用户信息
    user_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="用户飞书ID",
    )

    user_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="用户姓名",
    )

    # 会话信息
    chat_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="飞书会话ID",
    )

    chat_type: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="会话类型（p2p/group）",
    )

    # 状态
    state: Mapped[DialogState] = mapped_column(
        String(32),
        nullable=False,
        default=DialogState.ACTIVE,
        comment="会话状态",
    )

    # Skill相关
    matched_skill: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="匹配的Skill名称",
    )

    collected_params: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="已收集的参数（JSON）",
    )

    missing_params: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="缺失的参数列表（JSON）",
    )

    # 上下文
    context: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="会话上下文（JSON）",
    )

    # 轮次
    round_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="对话轮次",
    )

    # 关联消息
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="session",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ConversationSession(id={self.id}, user_id={self.user_id}, state={self.state})>"


class ConversationMessage(Base, AuditMixin):
    """
    对话消息实体.

    存储会话中的每条消息。

    Attributes:
        id: 消息ID
        session_id: 所属会话ID
        role: 消息角色
        content: 消息内容
        skill_name: 触发的Skill名称
        execution_id: Skill执行ID
    """

    __tablename__ = "conversation_messages"
    __table_args__ = (
        Index("ix_conversation_messages_session_id", "session_id"),
        Index("ix_conversation_messages_created_at", "created_at"),
        {"comment": "对话消息表"},
    )

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="消息ID",
    )

    # 会话ID
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话ID",
    )

    # 消息内容
    role: Mapped[ConversationRole] = mapped_column(
        String(32),
        nullable=False,
        comment="消息角色",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )

    # Skill相关
    skill_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="触发的Skill名称",
    )

    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Skill执行ID",
    )

    # 元数据
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="元数据（JSON）",
    )

    # 关联关系
    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<ConversationMessage(id={self.id}, role={self.role})>"