"""
PM Digital Employee - Access Control Service
项目经理数字员工系统 - 权限访问控制核心服务

实现项目级权限校验、用户角色权限管理、Skill访问控制。
"""

import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ErrorCode, PermissionError, ProjectAccessDeniedError, SkillAccessDeniedError
from app.core.logging import get_logger
from app.domain.enums import PermissionAction, PermissionResource, UserRole
from app.domain.models.user_project_role import UserProjectRole

logger = get_logger(__name__)


class AccessControlService:
    """
    权限访问控制服务.

    实现项目级权限校验、角色权限矩阵、Skill访问控制。
    采用默认拒绝原则，仅显式授权的操作可执行。
    """

    # 角色权限矩阵
    # 定义每个角色对每种资源的操作权限
    ROLE_PERMISSION_MATRIX: Dict[UserRole, Dict[str, List[str]]] = {
        UserRole.PROJECT_MANAGER: {
            # 项目经理拥有所有资源的所有权限
            "project": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "task": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "milestone": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "cost": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "risk": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "document": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "report": ["read", "write", "submit", "approve", "execute", "manage", "delete"],
            "approval": ["read", "write", "submit", "approve", "execute", "manage"],
            "knowledge": ["read", "write", "execute"],
            "skill": ["read", "execute"],
        },
        UserRole.PM: {
            # PM拥有大部分权限，但没有manage和delete权限
            "project": ["read", "write", "submit", "execute"],
            "task": ["read", "write", "submit", "execute"],
            "milestone": ["read", "write", "submit", "execute"],
            "cost": ["read", "write", "submit", "execute"],
            "risk": ["read", "write", "submit", "execute"],
            "document": ["read", "write", "submit", "execute"],
            "report": ["read", "write", "submit", "execute"],
            "approval": ["read", "submit"],
            "knowledge": ["read", "execute"],
            "skill": ["read", "execute"],
        },
        UserRole.TECH_LEAD: {
            # 技术负责人拥有读写和执行权限
            "project": ["read", "write"],
            "task": ["read", "write", "submit", "execute"],
            "milestone": ["read", "write", "submit"],
            "cost": ["read"],
            "risk": ["read", "write", "submit", "execute"],
            "document": ["read", "write", "submit", "execute"],
            "report": ["read", "write", "submit"],
            "approval": ["read", "submit"],
            "knowledge": ["read", "execute"],
            "skill": ["read", "execute"],
        },
        UserRole.MEMBER: {
            # 普通成员只有读取和提交权限
            "project": ["read"],
            "task": ["read", "submit"],
            "milestone": ["read"],
            "cost": [],
            "risk": ["read"],
            "document": ["read", "submit"],
            "report": ["read"],
            "approval": [],
            "knowledge": ["read"],
            "skill": ["read", "execute"],
        },
        UserRole.AUDITOR: {
            # 审计员只有读取权限
            "project": ["read"],
            "task": ["read"],
            "milestone": ["read"],
            "cost": ["read"],
            "risk": ["read"],
            "document": ["read"],
            "report": ["read"],
            "approval": ["read"],
            "knowledge": ["read"],
            "skill": ["read"],
        },
    }

    def __init__(self, session: AsyncSession, redis_client=None) -> None:
        """
        初始化权限控制服务.

        Args:
            session: 数据库会话
            redis_client: Redis客户端（用于缓存）
        """
        self.session = session
        self.redis_client = redis_client

    async def get_user_project_role(
        self,
        user_id: str,
        project_id: uuid.UUID,
    ) -> Optional[UserRole]:
        """
        获取用户在项目中的角色.

        Args:
            user_id: 飞书用户ID
            project_id: 项目ID

        Returns:
            Optional[UserRole]: 用户角色或None
        """
        # 先查缓存
        if self.redis_client:
            cache_key = f"user_role:{user_id}:{project_id}"
            cached_role = await self.redis_client.get(cache_key)
            if cached_role:
                return UserRole(cached_role)

        # 查询数据库
        from app.domain.models.user import User
        from app.domain.models.project import Project

        # 通过飞书用户ID查找用户
        user_result = await self.session.execute(
            select(User).where(User.feishu_user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return None

        # 查询用户项目角色
        role_result = await self.session.execute(
            select(UserProjectRole).where(
                UserProjectRole.user_id == user.id,
                UserProjectRole.project_id == project_id,
            )
        )
        user_role = role_result.scalar_one_or_none()

        if user_role:
            # 缓存角色
            if self.redis_client:
                cache_key = f"user_role:{user_id}:{project_id}"
                await self.redis_client.setex(
                    cache_key,
                    settings.permission.cache_ttl,
                    user_role.role.value,
                )
            return user_role.role

        return None

    async def verify_project_access(
        self,
        user_id: str,
        project_id: uuid.UUID,
        resource: str,
        action: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        验证用户对项目资源的访问权限.

        Args:
            user_id: 飞书用户ID
            project_id: 项目ID
            resource: 资源类型
            action: 操作类型

        Returns:
            Tuple[bool, Optional[str]]: (是否有权限, 拒绝原因)
        """
        # 获取用户角色
        role = await self.get_user_project_role(user_id, project_id)

        if role is None:
            return False, "用户不在项目中，无访问权限"

        # 检查权限矩阵
        role_permissions = self.ROLE_PERMISSION_MATRIX.get(role, {})
        resource_actions = role_permissions.get(resource, [])

        if action in resource_actions:
            logger.debug(
                "Permission granted",
                user_id=user_id,
                project_id=str(project_id),
                resource=resource,
                action=action,
                role=role.value,
            )
            return True, None

        logger.warning(
            "Permission denied",
            user_id=user_id,
            project_id=str(project_id),
            resource=resource,
            action=action,
            role=role.value,
        )
        return False, f"当前角色({role.value})无{resource}资源的{action}权限"

    async def check_skill_access(
        self,
        user_id: str,
        project_id: uuid.UUID,
        skill_name: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        检查用户是否有执行Skill的权限.

        Args:
            user_id: 飞书用户ID
            project_id: 项目ID
            skill_name: Skill名称

        Returns:
            Tuple[bool, Optional[str]]: (是否有权限, 拒绝原因)
        """
        from app.domain.models.skill_definition import ProjectSkillSwitch, SkillDefinition

        # 1. 检查Skill是否在当前项目启用
        skill_result = await self.session.execute(
            select(SkillDefinition).where(SkillDefinition.skill_name == skill_name)
        )
        skill = skill_result.scalar_one_or_none()

        if skill is None:
            return False, f"Skill {skill_name} 不存在"

        # 2. 检查项目级Skill开关
        switch_result = await self.session.execute(
            select(ProjectSkillSwitch).where(
                ProjectSkillSwitch.project_id == project_id,
                ProjectSkillSwitch.skill_id == skill.id,
            )
        )
        skill_switch = switch_result.scalar_one_or_none()

        # 如果有项目级配置，使用项目级配置；否则使用默认配置
        if skill_switch is not None and not skill_switch.is_enabled:
            return False, f"Skill {skill_name} 未在当前项目启用"

        if skill_switch is None and not skill.enabled_by_default:
            return False, f"Skill {skill_name} 未在当前项目启用"

        # 3. 检查用户角色是否在允许列表中
        import json

        try:
            allowed_roles = json.loads(skill.allowed_roles) if skill.allowed_roles else []
        except json.JSONDecodeError:
            allowed_roles = []

        user_role = await self.get_user_project_role(user_id, project_id)

        if user_role is None:
            return False, "用户不在项目中"

        if allowed_roles and user_role.value not in allowed_roles:
            return False, f"当前角色({user_role.value})无权执行此Skill"

        # 4. 检查所需权限
        try:
            required_permissions = json.loads(skill.required_permissions) if skill.required_permissions else []
        except json.JSONDecodeError:
            required_permissions = []

        for perm in required_permissions:
            resource = perm.get("resource")
            action = perm.get("action")
            if resource and action:
                has_perm, reason = await self.verify_project_access(
                    user_id, project_id, resource, action
                )
                if not has_perm:
                    return False, reason

        return True, None

    async def get_user_accessible_projects(
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

    async def enforce_group_project_binding(
        self,
        chat_id: str,
        project_id: uuid.UUID,
    ) -> Tuple[bool, Optional[str]]:
        """
        强制执行飞书群-项目绑定校验.

        确保群内操作只能访问绑定项目。

        Args:
            chat_id: 飞书群ID
            project_id: 待访问项目ID

        Returns:
            Tuple[bool, Optional[str]]: (是否通过, 拒绝原因)
        """
        from app.domain.models.group_project_binding import GroupProjectBinding

        result = await self.session.execute(
            select(GroupProjectBinding).where(
                GroupProjectBinding.chat_id == chat_id,
                GroupProjectBinding.is_active == True,
            )
        )
        binding = result.scalar_one_or_none()

        if binding is None:
            return False, "当前群未绑定项目"

        if binding.project_id != project_id:
            return False, "群绑定项目与请求项目不匹配，禁止跨项目访问"

        return True, None

    async def get_group_bound_project(
        self,
        chat_id: str,
    ) -> Optional[uuid.UUID]:
        """
        获取飞书群绑定的项目ID.

        Args:
            chat_id: 飞书群ID

        Returns:
            Optional[uuid.UUID]: 项目ID或None
        """
        from app.domain.models.group_project_binding import GroupProjectBinding

        result = await self.session.execute(
            select(GroupProjectBinding).where(
                GroupProjectBinding.chat_id == chat_id,
                GroupProjectBinding.is_active == True,
            )
        )
        binding = result.scalar_one_or_none()

        return binding.project_id if binding else None