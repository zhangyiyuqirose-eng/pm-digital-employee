"""
PM Digital Employee - Domain Base
项目经理数字员工系统 - 领域模型基类
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class AuditMixin:
    """审计混入类."""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), nullable=True)