"""
PM Digital Employee - Project Isolation Service
项目经理数字员工系统 - 项目隔离服务（核心安全模块）

确保用户绝对不能跨项目访问数据。
所有数据访问必须经过此服务校验。
这是PM机器人的最核心安全模块。

参考提示词Part 2.3标准实现。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ErrorCode,
    GroupNotBoundError,
    PermissionDeniedError,
    ProjectAccessDeniedError,
    ProjectNotFoundError,
)
from app.core.logging import get_logger
from app.domain.enums import PermissionAction, UserRole
from app.domain.models.group_project_binding import GroupProjectBinding
from app.domain.models.project import Project
from app.domain.models.user_project_role import UserProjectRole
from app.services.audit_service import AuditService

logger = get_logger(__name__)


class ProjectIsolationService:
    """
    项目隔离服务 - 核心安全模块.

    确保用户绝对不能跨项目访问数据。
    所有数据访问都必须经过此服务校验。

    核心原则：
    1. 群聊场景：群只能绑定一个项目，群内操作只能访问绑定项目
    2. 用户场景：用户必须是项目成员才能访问项目数据
    3. 所有查询必须携带project_id过滤条件
    """

    def __init__(
        self,
        session: AsyncSession,
        redis_client=None,
        audit_service: Optional[AuditService] = None,
    ) -> None:
        """
        初始化项目隔离服务.

        Args:
            session: 数据库会话
            redis_client: Redis客户端（用于缓存）
            audit_service: 审计服务
        """
        self.session = session
        self.redis_client = redis_client
        self._audit_service = audit_service or AuditService(session)

    async def enforce_chat_project_binding(
        self,
        chat_id: str,
        claimed_project_id: uuid.UUID,
    ) -> bool:
        """
        强制群-项目绑定校验.

        确保群聊中操作的项目就是绑定的项目，防止伪造project_id。

        Args:
            chat_id: 飞书群ID
            claimed_project_id: 用户声称要访问的项目ID

        Returns:
            bool: 是否通过校验

        Raises:
            GroupNotBoundError: 群未绑定项目
            ProjectAccessDeniedError: 项目ID不匹配
        """
        binding = await self.get_chat_project_binding(chat_id)

        if not binding:
            logger.warning(
                "Group not bound to any project",
                chat_id=chat_id,
                claimed_project_id=str(claimed_project_id),
            )
            raise GroupNotBoundError(chat_id=chat_id)

        if binding.project_id != claimed_project_id:
            logger.warning(
                "Project ID mismatch - cross-project access blocked",
                chat_id=chat_id,
                bound_project_id=str(binding.project_id),
                claimed_project_id=str(claimed_project_id),
            )
            raise ProjectAccessDeniedError(
                project_id=str(claimed_project_id),
                trace_id=None,
            )

        return True

    async def enforce_user_in_project(
        self,
        user_id: str,
        project_id: uuid.UUID,
    ) -> bool:
        """
        强制用户在项目中校验.

        即使群聊绑定了项目，用户也必须是该项目成员才能操作。

        Args:
            user_id: 飞书用户ID
            project_id: 项目ID

        Returns:
            bool: 是否通过校验

        Raises:
            ProjectAccessDeniedError: 用户不是项目成员
        """
        role_record = await self._get_user_project_role(user_id, project_id)

        if not role_record:
            logger.warning(
                "User not in project - access denied",
                user_id=user_id,
                project_id=str(project_id),
            )
            raise ProjectAccessDeniedError(
                project_id=str(project_id),
                user_id=user_id,
                trace_id=None,
            )

        return True

    async def get_chat_project_binding(
        self,
        chat_id: str,
    ) -> Optional[GroupProjectBinding]:
        """
        获取群-项目绑定（带缓存）.

        Args:
            chat_id: 飞书群ID

        Returns:
            Optional[GroupProjectBinding]: 绑定记录或None
        """
        # 优先从缓存获取
        if self.redis_client:
            cache_key = f"chat:project_binding:{chat_id}"
            import json

            cached = await self.redis_client.get(cache_key)
            if cached:
                try:
                    data = json.loads(cached)
                    return GroupProjectBinding(**data)
                except (json.JSONDecodeError, ValueError):
                    pass

        # 查询数据库
        result = await self.session.execute(
            select(GroupProjectBinding).where(
                and_(
                    GroupProjectBinding.chat_id == chat_id,
                    GroupProjectBinding.is_active == True,
                )
            )
        )
        binding = result.scalar_one_or_none()

        # 缓存绑定
        if binding and self.redis_client:
            import json

            cache_key = f"chat:project_binding:{chat_id}"
            binding_data = {
                "id": str(binding.id),
                "chat_id": binding.chat_id,
                "project_id": str(binding.project_id),
                "bound_by": binding.bound_by,
                "is_active": binding.is_active,
            }
            await self.redis_client.setex(
                cache_key,
                86400 * 7,  # 7天缓存
                json.dumps(binding_data),
            )

        return binding

    async def bind_chat_to_project(
        self,
        chat_id: str,
        project_id: uuid.UUID,
        bound_by: str,
    ) -> GroupProjectBinding:
        """
        绑定群聊到项目.

        Args:
            chat_id: 飞书群ID
            project_id: 项目ID
            bound_by: 操作人飞书用户ID

        Returns:
            GroupProjectBinding: 绑定记录

        Raises:
            ProjectNotFoundError: 项目不存在
            PermissionDeniedError: 操作人无权限
            ValueError: 群已绑定其他项目
        """
        # 1. 校验项目存在
        project_result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 2. 校验操作人是否有CONFIG权限
        # （这里简化处理，允许项目管理员和PM绑定）
        user_role = await self._get_user_project_role(bound_by, project_id)
        if not user_role or user_role.role not in [UserRole.PROJECT_MANAGER, UserRole.PM, UserRole.ADMIN]:
            raise PermissionDeniedError(
                message=f"用户 {bound_by} 无权绑定项目 {project_id}",
                trace_id=None,
            )

        # 3. 检查是否已绑定其他项目
        existing = await self.get_chat_project_binding(chat_id)
        if existing:
            raise ValueError(f"群聊已绑定项目 {existing.project_id}，请先解绑")

        # 4. 创建绑定
        binding = GroupProjectBinding(
            chat_id=chat_id,
            project_id=project_id,
            bound_by=bound_by,
            is_active=True,
        )
        self.session.add(binding)
        await self.session.commit()

        # 5. 清除缓存
        if self.redis_client:
            await self.redis_client.delete(f"chat:project_binding:{chat_id}")

        # 6. 记录审计日志
        await self._audit_service.log_action(
            user_id=bound_by,
            action="bind_chat_to_project",
            object_type="chat_project_binding",
            object_id=str(binding.id),
            details={"chat_id": chat_id, "project_id": str(project_id)},
        )

        logger.info(
            "Chat bound to project",
            chat_id=chat_id,
            project_id=str(project_id),
            bound_by=bound_by,
        )

        return binding

    async def unbind_chat(
        self,
        chat_id: str,
        operator_id: str,
    ) -> bool:
        """
        解绑群聊.

        Args:
            chat_id: 飞书群ID
            operator_id: 操作人飞书用户ID

        Returns:
            bool: 是否成功解绑

        Raises:
            PermissionDeniedError: 操作人无权限
        """
        binding = await self.get_chat_project_binding(chat_id)

        if not binding:
            return False  # 无绑定，无需解绑

        # 校验权限
        user_role = await self._get_user_project_role(operator_id, binding.project_id)
        if not user_role or user_role.role not in [UserRole.PROJECT_MANAGER, UserRole.PM, UserRole.ADMIN]:
            raise PermissionDeniedError(
                message="无权解绑",
                trace_id=None,
            )

        # 标记为不活跃（软删除）
        binding.is_active = False
        await self.session.commit()

        # 清除缓存
        if self.redis_client:
            await self.redis_client.delete(f"chat:project_binding:{chat_id}")

        # 记录审计日志
        await self._audit_service.log_action(
            user_id=operator_id,
            action="unbind_chat_from_project",
            object_type="chat_project_binding",
            object_id=str(binding.id),
            details={"chat_id": chat_id, "project_id": str(binding.project_id)},
        )

        logger.info(
            "Chat unbound from project",
            chat_id=chat_id,
            project_id=str(binding.project_id),
            operator_id=operator_id,
        )

        return True

    async def get_user_accessible_project_ids(
        self,
        user_id: str,
    ) -> List[uuid.UUID]:
        """
        获取用户可访问的所有项目ID列表.

        Args:
            user_id: 飞书用户ID

        Returns:
            List[uuid.UUID]: 项目ID列表
        """
        from app.domain.models.user import User

        # 查找用户
        user_result = await self.session.execute(
            select(User).where(User.feishu_user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        # 查询用户参与的所有项目
        result = await self.session.execute(
            select(UserProjectRole.project_id).where(UserProjectRole.user_id == user.id)
        )
        project_ids = [row[0] for row in result.fetchall()]

        return project_ids

    async def filter_query_by_user_projects(
        self,
        user_id: str,
        query: Any,
        project_id_field: Any,
    ) -> Any:
        """
        查询过滤器 - 自动给所有查询添加用户可访问项目的过滤条件.

        这是防止跨项目数据泄露的最后一道防线。

        Args:
            user_id: 飞书用户ID
            query: SQLAlchemy查询对象
            project_id_field: ORM模型的project_id字段

        Returns:
            Any: 添加过滤条件后的查询对象
        """
        accessible_project_ids = await self.get_user_accessible_project_ids(user_id)

        if not accessible_project_ids:
            # 无可访问项目，返回空查询
            return query.filter(project_id_field == None)

        return query.filter(project_id_field.in_(accessible_project_ids))

    async def _get_user_project_role(
        self,
        user_id: str,
        project_id: uuid.UUID,
    ) -> Optional[UserProjectRole]:
        """
        获取用户项目角色记录.

        Args:
            user_id: 飞书用户ID
            project_id: 项目ID

        Returns:
            Optional[UserProjectRole]: 角色记录或None
        """
        from app.domain.models.user import User

        # 查找用户
        user_result = await self.session.execute(
            select(User).where(User.feishu_user_id == user_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        # 查询角色
        role_result = await self.session.execute(
            select(UserProjectRole).where(
                and_(
                    UserProjectRole.user_id == user.id,
                    UserProjectRole.project_id == project_id,
                )
            )
        )
        return role_result.scalar_one_or_none()


# 全局服务实例（建议通过依赖注入获取）
_project_isolation_service: Optional[ProjectIsolationService] = None


def get_project_isolation_service() -> ProjectIsolationService:
    """
    获取项目隔离服务实例.

    注意：推荐使用依赖注入方式获取带session的服务实例。
    """
    global _project_isolation_service
    if _project_isolation_service is None:
        # 创建无session的基础实例
        _project_isolation_service = ProjectIsolationService(session=None)
    return _project_isolation_service


def init_project_isolation_service(
    session: AsyncSession,
    redis_client=None,
    audit_service: Optional[AuditService] = None,
) -> ProjectIsolationService:
    """
    初始化项目隔离服务（带数据库会话）.

    Args:
        session: 数据库会话
        redis_client: Redis客户端
        audit_service: 审计服务

    Returns:
        ProjectIsolationService: 服务实例
    """
    global _project_isolation_service
    _project_isolation_service = ProjectIsolationService(
        session=session,
        redis_client=redis_client,
        audit_service=audit_service,
    )
    return _project_isolation_service