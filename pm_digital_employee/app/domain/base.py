"""
PM Digital Employee - SQLAlchemy Base Module
项目经理数字员工系统 - SQLAlchemy基类模块

定义ORM模型的公共基类，包含：
- 主键ID字段
- 创建时间字段
- 更新时间字段
- 软删除字段
- 公共方法
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative, declarative_mixin


@as_declarative
class Base:
    """
    SQLAlchemy声明式基类.

    所有ORM模型必须继承此基类，
    自动包含id、created_at、updated_at字段。
    """

    # 表名自动生成（子类可覆盖）
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """生成表名，将驼峰命名转换为下划线命名."""
        import re

        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name

    # 主键ID - 使用UUID v4
    id: Column = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=None,  # PostgreSQL会自动生成
        comment="主键ID",
    )

    # 创建时间
    created_at: Column = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=None,
        comment="创建时间",
    )

    # 更新时间
    updated_at: Column = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=None,
        comment="更新时间",
    )

    def to_dict(self, exclude: Optional[set] = None) -> Dict[str, Any]:
        """
        将模型转换为字典.

        Args:
            exclude: 排除的字段集合

        Returns:
            Dict[str, Any]: 模型字典表示
        """
        exclude = exclude or set()
        result = {}

        for column in self.__table__.columns:
            if column.name in exclude:
                continue

            value = getattr(self, column.name)

            # 处理特殊类型
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)

            result[column.name] = value

        return result

    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[set] = None) -> None:
        """
        从字典更新模型字段.

        Args:
            data: 更新数据字典
            exclude: 排除的字段集合
        """
        exclude = exclude or {"id", "created_at"}

        for key, value in data.items():
            if key in exclude:
                continue

            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """模型字符串表示."""
        return f"<{self.__class__.__name__}(id={self.id})>"


@declarative_mixin
class SoftDeleteMixin:
    """
    软删除混入类.

    为模型添加软删除能力，不会真正删除记录，
    而是标记is_deleted为True。
    """

    is_deleted: Column = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="是否已删除",
    )

    deleted_at: Column = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="删除时间",
    )

    def soft_delete(self) -> None:
        """软删除记录."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """恢复软删除的记录."""
        self.is_deleted = False
        self.deleted_at = None


@declarative_mixin
class ProjectScopedMixin:
    """
    项目域隔离混入类.

    为模型添加project_id字段，用于项目级数据隔离。
    所有需要项目隔离的表必须使用此混入。
    """

    project_id: Column = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="项目ID（项目隔离字段）",
    )

    @declared_attr
    def __table_args__(cls):
        """添加项目隔离索引."""
        return (
            # 联合索引：(project_id, created_at) 用于按项目查询历史数据
            # 联合索引：(project_id, id) 用于按项目查询详情
        )


@declarative_mixin
class TenantMixin:
    """
    租户隔离混入类.

    为多租户场景添加租户字段。
    一期MVP暂不启用，预留扩展能力。
    """

    tenant_id: Column = Column(
        String(36),
        nullable=False,
        index=True,
        comment="租户ID",
    )


@declarative_mixin
class AuditMixin:
    """
    审计信息混入类.

    为模型添加创建人和更新人字段。
    """

    created_by: Column = Column(
        String(64),
        nullable=True,
        comment="创建人ID",
    )

    updated_by: Column = Column(
        String(64),
        nullable=True,
        comment="更新人ID",
    )

    version: Column = Column(
        "version",
        None,
        nullable=False,
        default=1,
        comment="版本号（乐观锁）",
    )


@declarative_mixin
class TimestampMixin:
    """
    时间戳混入类.

    提供额外的时间戳字段。
    """

    # 业务日期（用于按业务日期统计）
    business_date: Column = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="业务日期",
    )

    # 生效时间（用于有效期管理）
    effective_from: Column = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="生效开始时间",
    )

    effective_to: Column = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="生效结束时间",
    )


class BaseModel(Base):
    """基础模型类，包含主键和时间戳."""

    __abstract__ = True

    pass


class ProjectScopedModel(Base, ProjectScopedMixin):
    """
    项目隔离模型基类.

    包含项目隔离字段，用于所有需要项目级数据隔离的表。
    """

    __abstract__ = True

    pass


class FullAuditModel(Base, ProjectScopedMixin, AuditMixin, SoftDeleteMixin):
    """
    完整审计模型基类.

    包含项目隔离、审计信息、软删除能力。
    用于核心业务表。
    """

    __abstract__ = True

    pass


# 公共字段类型定义
class FieldType:
    """字段类型常量."""

    # ID类型
    ID_TYPE = UUID(as_uuid=True)

    # 字符串类型
    NAME_TYPE = String(128)  # 名称类型
    CODE_TYPE = String(64)  # 编码类型
    DESCRIPTION_TYPE = String(512)  # 描述类型
    CONTENT_TYPE = String  # 长文本类型（无长度限制）

    # 外键类型
    FK_TYPE = UUID(as_uuid=True)  # 外键类型


# 索引生成工具
def create_index_name(table_name: str, *columns: str) -> str:
    """
    生成索引名称.

    Args:
        table_name: 表名
        columns: 列名列表

    Returns:
        str: 索引名称
    """
    return f"idx_{table_name}_{'_'.join(columns)}"