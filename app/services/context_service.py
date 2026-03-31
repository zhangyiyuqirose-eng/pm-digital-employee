"""
PM Digital Employee - Context Service
项目经理数字员工系统 - 用户/项目上下文构建与管理服务

构建和管理用户上下文、项目上下文、会话上下文。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import GroupNotBoundError, ProjectAccessDeniedError
from app.core.logging import get_logger
from app.domain.enums import UserRole

logger = get_logger(__name__)


@dataclass
class UserContext:
    """
    用户上下文数据结构.

    包含用户信息、项目信息、权限信息等完整的上下文数据。

    Attributes:
        user_id: 飞书用户ID
        user_name: 用户姓名
        chat_id: 飞书会话ID
        chat_type: 会话类型（p2p/group）
        project_id: 当前项目ID
        user_role: 用户在当前项目的角色
        accessible_projects: 用户可访问的项目ID列表
        permissions: 用户权限列表
        trace_id: 追踪ID
        created_at: 上下文创建时间
    """

    user_id: str
    user_name: str = ""
    chat_id: str = ""
    chat_type: str = "p2p"  # p2p 或 group
    project_id: Optional[uuid.UUID] = None
    user_role: Optional[UserRole] = None
    accessible_projects: List[uuid.UUID] = field(default_factory=list)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    trace_id: str = ""
    extra: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict:
        """转换为字典格式."""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "chat_id": self.chat_id,
            "chat_type": self.chat_type,
            "project_id": str(self.project_id) if self.project_id else None,
            "user_role": self.user_role.value if self.user_role else None,
            "accessible_projects": [str(p) for p in self.accessible_projects],
            "permissions": self.permissions,
            "trace_id": self.trace_id,
            "extra": self.extra,
            "created_at": self.created_at.isoformat(),
        }


class ContextService:
    """
    上下文管理服务.

    构建和管理用户上下文、项目上下文、会话上下文。
    支持缓存以提升性能。
    """

    def __init__(self, session: AsyncSession, redis_client=None) -> None:
        """
        初始化上下文服务.

        Args:
            session: 数据库会话
            redis_client: Redis客户端（用于缓存）
        """
        self.session = session
        self.redis_client = redis_client

    async def build_user_context(
        self,
        user_id: str,
        chat_id: str,
        chat_type: str = "p2p",
    ) -> UserContext:
        """
        构建用户上下文.

        完整的上下文构建流程：
        1. 查询缓存
        2. 获取用户基础信息
        3. 获取群绑定的项目（群聊场景）
        4. 获取用户项目角色
        5. 获取可访问项目列表
        6. 构建并缓存上下文

        Args:
            user_id: 飞书用户ID
            chat_id: 飞书会话ID
            chat_type: 会话类型

        Returns:
            UserContext: 用户上下文

        Raises:
            GroupNotBoundError: 群未绑定项目
            ProjectAccessDeniedError: 用户无项目访问权限
        """
        logger.debug(
            "Building user context",
            user_id=user_id,
            chat_id=chat_id,
            chat_type=chat_type,
        )

        # 1. 检查缓存
        cache_key = f"context:{user_id}:{chat_id}"
        if self.redis_client:
            import json

            cached = await self.redis_client.get(cache_key)
            if cached:
                try:
                    data = json.loads(cached)
                    logger.debug("Context cache hit", user_id=user_id)
                    return UserContext(
                        user_id=data["user_id"],
                        user_name=data.get("user_name", ""),
                        chat_id=data["chat_id"],
                        chat_type=data.get("chat_type", "p2p"),
                        project_id=uuid.UUID(data["project_id"]) if data.get("project_id") else None,
                        user_role=UserRole(data["user_role"]) if data.get("user_role") else None,
                        accessible_projects=[uuid.UUID(p) for p in data.get("accessible_projects", [])],
                        permissions=data.get("permissions", {}),
                        trace_id=data.get("trace_id", ""),
                        extra=data.get("extra", {}),
                    )
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass  # 缓存解析失败，继续构建

        # 2. 获取用户基础信息
        from app.domain.models.user import User

        user_result = await self.session.execute(
            select(User).where(User.feishu_user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        user_name = user.name if user else user_id

        # 3. 获取项目ID（群聊场景从群绑定获取）
        project_id: Optional[uuid.UUID] = None
        user_role: Optional[UserRole] = None

        if chat_type == "group":
            # 群聊场景：从群绑定获取项目
            from app.domain.models.group_project_binding import GroupProjectBinding

            binding_result = await self.session.execute(
                select(GroupProjectBinding).where(
                    GroupProjectBinding.chat_id == chat_id,
                    GroupProjectBinding.is_active == True,
                )
            )
            binding = binding_result.scalar_one_or_none()

            if not binding:
                raise GroupNotBoundError(chat_id=chat_id)

            project_id = binding.project_id
        else:
            # 单聊场景：使用用户的第一个可访问项目或让用户选择
            from app.domain.models.user_project_role import UserProjectRole

            if user:
                role_result = await self.session.execute(
                    select(UserProjectRole)
                    .where(UserProjectRole.user_id == user.id)
                    .limit(1)
                )
                first_role = role_result.scalar_one_or_none()
                if first_role:
                    project_id = first_role.project_id

        # 4. 获取用户项目角色
        if project_id and user:
            from app.domain.models.user_project_role import UserProjectRole

            role_result = await self.session.execute(
                select(UserProjectRole).where(
                    UserProjectRole.user_id == user.id,
                    UserProjectRole.project_id == project_id,
                )
            )
            user_project_role = role_result.scalar_one_or_none()
            if user_project_role:
                user_role = user_project_role.role

        # 5. 获取可访问项目列表
        accessible_projects: List[uuid.UUID] = []
        if user:
            from app.domain.models.user_project_role import UserProjectRole

            projects_result = await self.session.execute(
                select(UserProjectRole.project_id).where(UserProjectRole.user_id == user.id)
            )
            accessible_projects = [row[0] for row in projects_result.fetchall()]

        # 6. 构建上下文
        context = UserContext(
            user_id=user_id,
            user_name=user_name,
            chat_id=chat_id,
            chat_type=chat_type,
            project_id=project_id,
            user_role=user_role,
            accessible_projects=accessible_projects,
        )

        # 7. 缓存上下文
        if self.redis_client:
            import json

            await self.redis_client.setex(
                cache_key,
                settings.session.context_ttl,
                json.dumps(context.to_dict()),
            )

        logger.debug(
            "Context built",
            user_id=user_id,
            project_id=str(project_id),
            role=user_role.value if user_role else None,
        )

        return context

    async def get_project_context(
        self,
        project_id: uuid.UUID,
    ) -> Dict:
        """
        获取项目上下文.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 项目上下文数据
        """
        from app.domain.models.project import Project

        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return {}

        return {
            "project_id": str(project.id),
            "project_name": project.name,
            "project_code": project.code,
            "project_status": project.status,
            "pm_id": str(project.pm_id) if project.pm_id else None,
            "pm_name": project.pm_name,
        }

    async def clear_context_cache(
        self,
        user_id: str,
        chat_id: str,
    ) -> None:
        """
        清除上下文缓存.

        Args:
            user_id: 飞书用户ID
            chat_id: 飞书会话ID
        """
        if self.redis_client:
            cache_key = f"context:{user_id}:{chat_id}"
            await self.redis_client.delete(cache_key)
            logger.debug("Context cache cleared", user_id=user_id)