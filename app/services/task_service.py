"""
PM Digital Employee - Task Service
项目经理数字员工系统 - 任务业务服务

v1.2.0新增：
- Excel批量导入/导出任务
- 飞书表格同步任务数据
- 任务依赖关系设置
- 自动调整依赖任务时间
- 延期风险检测（同步到风险预警模块）
- 任务标签和筛选功能
"""

import json
import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, TaskNotFoundError, ProjectNotFoundError
from app.core.logging import get_logger
from app.domain.enums import TaskStatus, TaskPriority, DependencyType
from app.domain.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.repositories.project_repository import ProjectRepository

logger = get_logger(__name__)


class TaskService:
    """
    任务业务服务.

    封装任务相关的业务逻辑，包括任务的创建、更新、查询、删除，
    以及v1.2.0新增的Excel导入导出、飞书表格同步、依赖关系管理、延期检测等功能。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化任务服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._repository = TaskRepository(session)
        self._project_repository = ProjectRepository(session)

    # ==================== 基础任务操作 ====================

    async def create_task(
        self,
        project_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        assignee_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.PENDING,
        estimated_hours: Optional[Decimal] = None,
        deliverable: Optional[str] = None,
        parent_task_id: Optional[uuid.UUID] = None,
        predecessor_task_id: Optional[uuid.UUID] = None,
        dependency_type: Optional[str] = "FS",
        estimated_duration: Optional[int] = None,
        tags: Optional[List[str]] = None,
        data_source: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Task:
        """
        创建任务.

        Args:
            project_id: 项目ID（必填）
            name: 任务名称（必填）
            description: 任务描述
            assignee_id: 负责人飞书用户ID
            assignee_name: 负责人姓名
            start_date: 计划开始日期
            end_date: 计划结束日期
            priority: 任务优先级
            status: 任务状态
            estimated_hours: 预估工时
            deliverable: 交付物描述
            parent_task_id: 父任务ID
            predecessor_task_id: 前置任务ID（v1.2.0新增）
            dependency_type: 依赖类型（v1.2.0新增）
            estimated_duration: 预计工期天数（v1.2.0新增）
            tags: 任务标签列表（v1.2.0新增）
            data_source: 数据来源（v1.2.0新增）
            user_id: 创建用户ID

        Returns:
            Task: 创建的任务

        Raises:
            ProjectNotFoundError: 项目不存在
        """
        # 验证项目存在
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id=str(project_id))

        # 生成任务编码
        code = await self._repository.generate_task_code(project_id)

        # 如果设置了前置任务，自动调整开始时间
        if predecessor_task_id and start_date:
            start_date = await self._adjust_start_date_by_predecessor(
                predecessor_task_id, start_date, dependency_type
            )

        # 如果有预计工期但没有结束日期，自动计算结束日期
        if start_date and estimated_duration and not end_date:
            end_date = start_date + timedelta(days=estimated_duration)

        # 创建任务数据
        task_data = {
            "id": uuid.uuid4(),
            "project_id": project_id,
            "code": code,
            "name": name,
            "description": description,
            "assignee_id": assignee_id,
            "assignee_name": assignee_name,
            "start_date": start_date,
            "end_date": end_date,
            "priority": priority,
            "status": status,
            "progress": 0,
            "estimated_hours": estimated_hours,
            "deliverable": deliverable,
            "parent_task_id": parent_task_id,
            "predecessor_task_id": predecessor_task_id,
            "dependency_type": dependency_type,
            "estimated_duration": estimated_duration,
            "data_source": data_source or "lark_card",
        }

        # 设置标签
        if tags:
            task_data["tags"] = json.dumps(tags)

        task = await self._repository.create_in_project(project_id, task_data)

        # 如果设置了前置任务，更新前置任务的后置任务列表
        if predecessor_task_id:
            await self._add_successor_to_predecessor(predecessor_task_id, str(task.id))

        logger.info(
            "Task created",
            extra={
                "task_id": str(task.id),
                "project_id": str(project_id),
                "name": name,
                "assignee_id": assignee_id,
                "predecessor_task_id": str(predecessor_task_id) if predecessor_task_id else None,
            }
        )

        return task

    async def get_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Task:
        """
        获取任务信息.

        Args:
            task_id: 任务ID
            project_id: 项目ID（用于权限检查）

        Returns:
            Task: 任务对象

        Raises:
            TaskNotFoundError: 任务不存在
        """
        task = await self._repository.get_by_id_or_error(task_id, project_id)
        return task

    async def update_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        **kwargs,
    ) -> Task:
        """
        更新任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID（用于权限检查）
            **kwargs: 更新字段

        Returns:
            Task: 更新后的任务

        Raises:
            TaskNotFoundError: 任务不存在
        """
        task = await self._repository.update_in_project(task_id, project_id, kwargs)

        logger.info(
            "Task updated",
            extra={
                "task_id": str(task_id),
                "project_id": str(project_id),
                "fields": list(kwargs.keys()),
            }
        )

        return task

    async def update_task_progress(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        progress: int,
        status: Optional[TaskStatus] = None,
    ) -> Task:
        """
        更新任务进度.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            progress: 进度值（0-100）
            status: 任务状态（可选）

        Returns:
            Task: 更新后的任务
        """
        update_data = {"progress": progress}

        # 根据进度自动更新状态
        if status:
            update_data["status"] = status
        elif progress == 100:
            update_data["status"] = TaskStatus.COMPLETED
            update_data["actual_end_date"] = date.today()
        elif progress > 0:
            update_data["status"] = TaskStatus.IN_PROGRESS
            if "actual_start_date" not in update_data:
                update_data["actual_start_date"] = date.today()

        return await self.update_task(task_id, project_id, **update_data)

    async def complete_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        actual_hours: Optional[Decimal] = None,
    ) -> Task:
        """
        完成任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            actual_hours: 实际工时

        Returns:
            Task: 更新后的任务
        """
        update_data = {
            "status": TaskStatus.COMPLETED,
            "progress": 100,
            "actual_end_date": date.today(),
        }

        if actual_hours:
            update_data["actual_hours"] = actual_hours

        task = await self.update_task(task_id, project_id, **update_data)

        # 任务完成后，自动调整后置任务的开始时间
        await self._adjust_successor_tasks_start_date(task)

        return task

    async def list_tasks(
        self,
        project_id: uuid.UUID,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        列出任务.

        Args:
            project_id: 项目ID
            status: 任务状态过滤
            assignee_id: 贌责人过滤
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 任务列表
        """
        filters = {}
        if status:
            filters["status"] = status
        if assignee_id:
            filters["assignee_id"] = assignee_id

        return await self._repository.list_by_project(
            project_id=project_id,
            filters=filters,
            skip=skip,
            limit=limit,
        )

    async def get_task_statistics(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, int]:
        """
        获取任务统计.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 统计信息
        """
        return await self._repository.get_statistics(project_id)

    async def delete_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> bool:
        """
        删除任务.

        Args:
            task_id: 任务ID
            project_id: 项目ID

        Returns:
            bool: 是否删除成功
        """
        # 删除前清理依赖关系
        task = await self.get_task(task_id, project_id)

        # 清理前置任务中的后置任务引用
        if task.predecessor_task_id:
            await self._remove_successor_from_predecessor(
                task.predecessor_task_id, str(task_id)
            )

        # 清理后置任务中的前置任务引用
        for successor_id in task.successor_ids_list:
            try:
                successor_uuid = uuid.UUID(successor_id)
                await self.update_task(
                    successor_uuid,
                    project_id,
                    predecessor_task_id=None,
                    dependency_type=None,
                )
            except (ValueError, TaskNotFoundError):
                pass

        return await self._repository.delete_in_project(task_id, project_id)

    # ==================== v1.2.0新增：任务依赖关系管理 ====================

    async def set_task_dependency(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        predecessor_task_id: uuid.UUID,
        dependency_type: str = "FS",
        adjust_dates: bool = True,
    ) -> Task:
        """
        设置任务依赖关系.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            predecessor_task_id: 前置任务ID
            dependency_type: 依赖类型（FS/SS/FF/SF）
            adjust_dates: 是否自动调整日期

        Returns:
            Task: 更新后的任务

        Raises:
            TaskNotFoundError: 任务不存在
            ValueError: 依赖关系无效（如循环依赖）
        """
        # 验证前置任务存在
        predecessor = await self.get_task(predecessor_task_id, project_id)

        # 检查是否形成循环依赖
        if await self._has_circular_dependency(task_id, predecessor_task_id):
            raise ValueError("设置依赖关系会导致循环依赖")

        # 清理旧的前置任务引用
        task = await self.get_task(task_id, project_id)
        if task.predecessor_task_id:
            await self._remove_successor_from_predecessor(
                task.predecessor_task_id, str(task_id)
            )

        # 设置新的依赖关系
        update_data = {
            "predecessor_task_id": predecessor_task_id,
            "dependency_type": dependency_type,
        }

        # 如果需要，自动调整日期
        if adjust_dates and task.start_date:
            new_start_date = await self._adjust_start_date_by_predecessor(
                predecessor_task_id, task.start_date, dependency_type
            )
            update_data["start_date"] = new_start_date

            # 如果有预计工期，更新结束日期
            if task.estimated_duration:
                update_data["end_date"] = new_start_date + timedelta(days=task.estimated_duration)

        task = await self.update_task(task_id, project_id, **update_data)

        # 更新前置任务的后置任务列表
        await self._add_successor_to_predecessor(predecessor_task_id, str(task_id))

        logger.info(
            "Task dependency set",
            extra={
                "task_id": str(task_id),
                "predecessor_task_id": str(predecessor_task_id),
                "dependency_type": dependency_type,
            }
        )

        return task

    async def remove_task_dependency(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Task:
        """
        移除任务依赖关系.

        Args:
            task_id: 任务ID
            project_id: 项目ID

        Returns:
            Task: 更新后的任务
        """
        task = await self.get_task(task_id, project_id)

        if task.predecessor_task_id:
            # 清理前置任务中的后置任务引用
            await self._remove_successor_from_predecessor(
                task.predecessor_task_id, str(task_id)
            )

            # 移除依赖关系
            task = await self.update_task(
                task_id,
                project_id,
                predecessor_task_id=None,
                dependency_type=None,
            )

        return task

    async def get_task_dependencies(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取任务的依赖关系信息.

        Args:
            task_id: 任务ID
            project_id: 项目ID

        Returns:
            Dict: 包含前置任务和后置任务信息
        """
        task = await self.get_task(task_id, project_id)

        result = {
            "task_id": str(task_id),
            "predecessor": None,
            "successors": [],
        }

        # 获取前置任务信息
        if task.predecessor_task_id:
            try:
                predecessor = await self.get_task(task.predecessor_task_id, project_id)
                result["predecessor"] = {
                    "id": str(predecessor.id),
                    "name": predecessor.name,
                    "status": predecessor.status,
                    "end_date": str(predecessor.end_date) if predecessor.end_date else None,
                    "dependency_type": task.dependency_type,
                }
            except TaskNotFoundError:
                result["predecessor"] = {"id": str(task.predecessor_task_id), "error": "not_found"}

        # 获取后置任务信息
        for successor_id in task.successor_ids_list:
            try:
                successor_uuid = uuid.UUID(successor_id)
                successor = await self.get_task(successor_uuid, project_id)
                result["successors"].append({
                    "id": str(successor.id),
                    "name": successor.name,
                    "status": successor.status,
                    "dependency_type": successor.dependency_type,
                })
            except (ValueError, TaskNotFoundError):
                result["successors"].append({"id": successor_id, "error": "not_found"})

        return result

    async def _adjust_start_date_by_predecessor(
        self,
        predecessor_task_id: uuid.UUID,
        current_start_date: date,
        dependency_type: str,
    ) -> date:
        """
        根据前置任务状态和依赖类型调整开始日期.

        Args:
            predecessor_task_id: 前置任务ID
            current_start_date: 当前开始日期
            dependency_type: 依赖类型

        Returns:
            date: 调整后的开始日期
        """
        result = await self.session.execute(
            select(Task).where(Task.id == predecessor_task_id)
        )
        predecessor = result.scalar_one_or_none()

        if not predecessor:
            return current_start_date

        # FS (完成-开始): 前置任务完成后才能开始
        if dependency_type == "FS":
            if predecessor.status == TaskStatus.COMPLETED and predecessor.actual_end_date:
                # 前置任务已完成，使用实际完成日期的第二天作为开始日期
                return predecessor.actual_end_date + timedelta(days=1)
            elif predecessor.end_date:
                # 前置任务未完成，使用计划结束日期的第二天作为开始日期
                return predecessor.end_date + timedelta(days=1)

        # SS (开始-开始): 前置任务开始后才能开始
        elif dependency_type == "SS":
            if predecessor.actual_start_date:
                return predecessor.actual_start_date
            elif predecessor.start_date:
                return predecessor.start_date

        # FF (完成-完成): 前置任务完成时本任务也要完成（不调整开始日期）
        # SF (开始-完成): 前置任务开始时本任务要完成（不调整开始日期）

        return current_start_date

    async def _adjust_successor_tasks_start_date(
        self,
        task: Task,
    ) -> None:
        """
        任务完成后，自动调整后置任务的开始时间.

        Args:
            task: 已完成的任务
        """
        if task.dependency_type != "FS" or not task.actual_end_date:
            return

        for successor_id in task.successor_ids_list:
            try:
                successor_uuid = uuid.UUID(successor_id)
                result = await self.session.execute(
                    select(Task).where(Task.id == successor_uuid)
                )
                successor = result.scalar_one_or_none()

                if successor and successor.dependency_type == "FS":
                    new_start_date = task.actual_end_date + timedelta(days=1)
                    
                    # 只有当新开始日期比原计划开始日期更晚时才调整
                    if successor.start_date and new_start_date > successor.start_date:
                        await self.update_task(
                            successor_uuid,
                            successor.project_id,
                            start_date=new_start_date,
                        )

                        if successor.estimated_duration:
                            new_end_date = new_start_date + timedelta(days=successor.estimated_duration)
                            await self.update_task(
                                successor_uuid,
                                successor.project_id,
                                end_date=new_end_date,
                            )

                        logger.info(
                            "Successor task start date adjusted",
                            extra={
                                "successor_task_id": str(successor_uuid),
                                "new_start_date": str(new_start_date),
                                "predecessor_task_id": str(task.id),
                            }
                        )

            except (ValueError, Exception) as e:
                logger.warning(f"Failed to adjust successor task: {e}")

    async def _add_successor_to_predecessor(
        self,
        predecessor_task_id: uuid.UUID,
        successor_id: str,
    ) -> None:
        """
        将当前任务添加到前置任务的后置任务列表中.

        Args:
            predecessor_task_id: 前置任务ID
            successor_id: 后置任务ID（字符串）
        """
        result = await self.session.execute(
            select(Task).where(Task.id == predecessor_task_id)
        )
        predecessor = result.scalar_one_or_none()

        if predecessor:
            successor_ids = predecessor.successor_ids_list
            if successor_id not in successor_ids:
                successor_ids.append(successor_id)
                predecessor.set_successor_ids(successor_ids)
                await self.session.flush()

    async def _remove_successor_from_predecessor(
        self,
        predecessor_task_id: uuid.UUID,
        successor_id: str,
    ) -> None:
        """
        从前置任务的后置任务列表中移除当前任务.

        Args:
            predecessor_task_id: 前置任务ID
            successor_id: 后置任务ID（字符串）
        """
        result = await self.session.execute(
            select(Task).where(Task.id == predecessor_task_id)
        )
        predecessor = result.scalar_one_or_none()

        if predecessor:
            successor_ids = predecessor.successor_ids_list
            if successor_id in successor_ids:
                successor_ids.remove(successor_id)
                predecessor.set_successor_ids(successor_ids if successor_ids else None)
                await self.session.flush()

    async def _has_circular_dependency(
        self,
        task_id: uuid.UUID,
        new_predecessor_id: uuid.UUID,
    ) -> bool:
        """
        检查是否形成循环依赖.

        Args:
            task_id: 当前任务ID
            new_predecessor_id: 新的前置任务ID

        Returns:
            bool: 是否存在循环依赖
        """
        # 如果新前置任务的后续链中包含当前任务，则形成循环
        visited = set()
        current_id = new_predecessor_id

        while current_id:
            if current_id == task_id:
                return True

            if current_id in visited:
                break

            visited.add(current_id)

            # 获取当前任务的前置任务
            result = await self.session.execute(
                select(Task.predecessor_task_id).where(Task.id == current_id)
            )
            current_id = result.scalar_one_or_none()

        return False

    # ==================== v1.2.0新增：延期检测和风险同步 ====================

    async def detect_delayed_tasks(
        self,
        project_id: uuid.UUID,
    ) -> List[Task]:
        """
        检测延期任务.

        Args:
            project_id: 项目ID

        Returns:
            List[Task]: 延期任务列表
        """
        return await self._repository.list_delayed_tasks(project_id)

    async def check_and_create_delay_risks(
        self,
        project_id: uuid.UUID,
    ) -> List[Dict[str, Any]]:
        """
        检查延期任务并创建风险记录.

        Args:
            project_id: 项目ID

        Returns:
            List[Dict]: 创建的风险记录列表
        """
        delayed_tasks = await self.detect_delayed_tasks(project_id)
        created_risks = []

        for task in delayed_tasks:
            # 检查是否已存在该任务的延期风险记录
            existing_risk = await self._check_existing_delay_risk(project_id, task.id)

            if not existing_risk:
                # 创建新的风险记录
                risk = await self._create_delay_risk(project_id, task)
                created_risks.append({
                    "risk_id": str(risk.id),
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "delay_days": task.get_delay_days(),
                })

        logger.info(
            "Delay risks created",
            extra={
                "project_id": str(project_id),
                "delayed_tasks_count": len(delayed_tasks),
                "risks_created_count": len(created_risks),
            }
        )

        return created_risks

    async def _check_existing_delay_risk(
        self,
        project_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> bool:
        """
        检查是否已存在任务的延期风险记录.

        Args:
            project_id: 项目ID
            task_id: 任务ID

        Returns:
            bool: 是否存在风险记录
        """
        from app.domain.models.risk import ProjectRisk
        from app.domain.enums import RiskCategory

        result = await self.session.execute(
            select(ProjectRisk).where(
                and_(
                    ProjectRisk.project_id == project_id,
                    ProjectRisk.category == RiskCategory.SCHEDULE,
                    ProjectRisk.title.contains(f"任务延期"),
                    ProjectRisk.description.contains(str(task_id)),
                    ProjectRisk.status.notin_(["resolved", "closed"]),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _create_delay_risk(
        self,
        project_id: uuid.UUID,
        task: Task,
    ) -> Any:
        """
        创建任务延期风险记录.

        Args:
            project_id: 项目ID
            task: 延期的任务

        Returns:
            ProjectRisk: 创建的风险记录
        """
        from app.services.risk_service import RiskService
        from app.domain.enums import RiskLevel, RiskCategory

        risk_service = RiskService(self.session)

        # 根据延期天数确定风险等级
        delay_days = task.get_delay_days()
        if delay_days >= 14:
            level = RiskLevel.CRITICAL
        elif delay_days >= 7:
            level = RiskLevel.HIGH
        elif delay_days >= 3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        title = f"任务延期风险: {task.name}"
        description = f"任务 '{task.name}' (ID: {task.id}) 已延期 {delay_days} 天。计划结束日期: {task.end_date}，当前进度: {task.progress}%"

        risk = await risk_service.create_risk(
            project_id=project_id,
            title=title,
            description=description,
            level=level,
            category=RiskCategory.SCHEDULE,
            probability=4,  # 已发生，概率高
            impact=3 if level in [RiskLevel.LOW, RiskLevel.MEDIUM] else 4,
            mitigation_plan="建议：1. 分析延期原因；2. 评估对项目整体进度的影响；3. 调整资源分配或计划",
            owner_id=task.assignee_id,
            owner_name=task.assignee_name,
            due_date=date.today() + timedelta(days=7),  # 建议在7天内处理
        )

        return risk

    # ==================== v1.2.0新增：任务标签管理 ====================

    async def add_task_tag(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        tag: str,
    ) -> Task:
        """
        添加任务标签.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            tag: 标签名称

        Returns:
            Task: 更新后的任务
        """
        task = await self.get_task(task_id, project_id)
        task.add_tag(tag)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def remove_task_tag(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        tag: str,
    ) -> Task:
        """
        移除任务标签.

        Args:
            task_id: 任务ID
            project_id: 项目ID
            tag: 标签名称

        Returns:
            Task: 更新后的任务
        """
        task = await self.get_task(task_id, project_id)
        task.remove_tag(tag)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def list_tasks_by_tag(
        self,
        project_id: uuid.UUID,
        tag: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """
        按标签筛选任务.

        Args:
            project_id: 项目ID
            tag: 标签名称
            skip: 跳过数量
            limit: 返回数量

        Returns:
            List[Task]: 任务列表
        """
        # 使用JSON contains查询
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.tags.contains(json.dumps(tag)),
                )
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_tags(
        self,
        project_id: uuid.UUID,
    ) -> List[str]:
        """
        获取项目所有使用的标签.

        Args:
            project_id: 项目ID

        Returns:
            List[str]: 标签列表
        """
        result = await self.session.execute(
            select(Task.tags).where(
                and_(
                    Task.project_id == project_id,
                    Task.tags.isnot(None),
                )
            )
        )
        tags_rows = result.scalars().all()

        all_tags = set()
        for tags_json in tags_rows:
            try:
                tags_list = json.loads(tags_json)
                all_tags.update(tags_list)
            except json.JSONDecodeError:
                pass

        return sorted(list(all_tags))

    # ==================== v1.2.0新增：Excel批量导入导出 ====================

    async def import_tasks_from_excel(
        self,
        file_path: str,
        project_id: uuid.UUID,
        import_mode: str = "incremental_update",
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从Excel批量导入任务.

        Args:
            file_path: Excel文件路径
            project_id: 项目ID
            import_mode: 导入模式（full_replace/incremental_update/append_only）
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Dict: 导入结果统计
        """
        from app.services.excel_service import ExcelService

        excel_service = ExcelService(self.session)

        # 解析Excel文件
        data_list, row_errors = excel_service.parse_excel(file_path, "task")

        # 为每条数据设置项目ID和数据来源
        for data in data_list:
            data["project_id"] = project_id
            data["data_source"] = "excel_import"

        # 执行导入
        import_log = await excel_service.import_data(
            data_list=data_list,
            module="task",
            import_mode=import_mode,
            project_id=project_id,
            user_id=operator_id,
        )

        # 检查延期并创建风险
        await self.check_and_create_delay_risks(project_id)

        return {
            "total": import_log.rows_total,
            "imported": import_log.rows_imported,
            "updated": import_log.rows_updated,
            "failed": import_log.rows_failed,
            "validation_errors": json.loads(import_log.validation_errors) if import_log.validation_errors else [],
        }

    async def export_tasks_to_excel(
        self,
        project_id: uuid.UUID,
    ) -> BytesIO:
        """
        导出任务为Excel.

        Args:
            project_id: 项目ID

        Returns:
            BytesIO: Excel文件流
        """
        from app.services.excel_service import ExcelService

        excel_service = ExcelService(self.session)
        return await excel_service.export_data("task", project_id)

    async def batch_update_status(
        self,
        project_id: uuid.UUID,
        task_ids: List[str],
        new_status: TaskStatus,
        operator_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量更新任务状态.

        Args:
            project_id: 项目ID
            task_ids: 任务ID列表
            new_status: 新状态
            operator_id: 操作人ID

        Returns:
            Dict: 更新结果统计
        """
        updated_count = 0
        failed_count = 0
        errors = []

        for task_id_str in task_ids:
            try:
                task_uuid = uuid.UUID(task_id_str)
                update_data = {"status": new_status}

                # 如果状态变为已完成，设置进度和结束日期
                if new_status == TaskStatus.COMPLETED:
                    update_data["progress"] = 100
                    update_data["actual_end_date"] = date.today()

                await self.update_task(task_uuid, project_id, **update_data)
                updated_count += 1
            except (ValueError, TaskNotFoundError) as e:
                failed_count += 1
                errors.append({"task_id": task_id_str, "error": str(e)})

        # 如果有任务完成，检查是否需要调整后置任务
        if new_status == TaskStatus.COMPLETED:
            for task_id_str in task_ids:
                try:
                    task_uuid = uuid.UUID(task_id_str)
                    task = await self.get_task(task_uuid, project_id)
                    await self._adjust_successor_tasks_start_date(task)
                except Exception:
                    pass

        # 检查延期并创建风险
        if new_status != TaskStatus.COMPLETED:
            await self.check_and_create_delay_risks(project_id)

        return {
            "updated": updated_count,
            "failed": failed_count,
            "errors": errors[:10],
        }

    # ==================== v1.2.0新增：飞书表格同步 ====================

    async def sync_tasks_from_lark_sheet(
        self,
        binding_id: uuid.UUID,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从飞书表格同步任务数据.

        Args:
            binding_id: 飞书表格绑定配置ID
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Dict: 同步结果统计
        """
        from app.services.lark_sheet_sync_service import LarkSheetSyncService

        sync_service = LarkSheetSyncService(self.session)
        result = await sync_service.sync_from_sheet(
            binding_id=binding_id,
            operator_id=operator_id,
            operator_name=operator_name,
        )

        # 获取绑定配置中的项目ID
        binding = await sync_service.sync_engine.get_lark_sheet_binding(binding_id)
        if binding and binding.project_id:
            # 检查延期并创建风险
            await self.check_and_create_delay_risks(binding.project_id)

        return result

    async def sync_tasks_to_lark_sheet(
        self,
        binding_id: uuid.UUID,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        将任务数据同步到飞书表格.

        Args:
            binding_id: 飞书表格绑定配置ID
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            Dict: 同步结果统计
        """
        from app.services.lark_sheet_sync_service import LarkSheetSyncService

        sync_service = LarkSheetSyncService(self.session)
        return await sync_service.sync_to_sheet(
            binding_id=binding_id,
            operator_id=operator_id,
            operator_name=operator_name,
        )

    # ==================== v1.2.0新增：任务进度计算 ====================

    async def calculate_project_progress(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        计算项目整体进度.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 进度统计信息
        """
        tasks = await self.list_tasks(project_id, limit=1000)

        if not tasks:
            return {
                "total_tasks": 0,
                "overall_progress": 0,
                "by_status": {},
            }

        # 按状态统计
        by_status = {}
        total_progress = 0

        for task in tasks:
            status = task.status
            if status not in by_status:
                by_status[status] = {"count": 0, "avg_progress": 0, "total_progress": 0}

            by_status[status]["count"] += 1
            by_status[status]["total_progress"] += task.calculate_progress_percentage()
            total_progress += task.calculate_progress_percentage()

        # 计算平均进度
        for status in by_status:
            count = by_status[status]["count"]
            by_status[status]["avg_progress"] = round(by_status[status]["total_progress"] / count, 1)

        overall_progress = round(total_progress / len(tasks), 1)

        return {
            "total_tasks": len(tasks),
            "overall_progress": overall_progress,
            "by_status": by_status,
            "delayed_count": len([t for t in tasks if t.is_delayed]),
        }

    async def get_delayed_tasks_report(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取延期任务报告.

        Args:
            project_id: 项目ID

        Returns:
            Dict: 延期任务报告
        """
        delayed_tasks = await self.detect_delayed_tasks(project_id)

        report = {
            "project_id": str(project_id),
            "delayed_count": len(delayed_tasks),
            "tasks": [],
            "high_risk_count": 0,
            "critical_risk_count": 0,
        }

        for task in delayed_tasks:
            delay_days = task.get_delay_days()
            task_info = {
                "id": str(task.id),
                "name": task.name,
                "status": task.status,
                "progress": task.progress,
                "end_date": str(task.end_date) if task.end_date else None,
                "delay_days": delay_days,
                "assignee_name": task.assignee_name,
                "priority": task.priority,
                "risk_level": "low",
            }

            # 判断风险等级
            if delay_days >= 14:
                task_info["risk_level"] = "critical"
                report["critical_risk_count"] += 1
            elif delay_days >= 7:
                task_info["risk_level"] = "high"
                report["high_risk_count"] += 1

            report["tasks"].append(task_info)

        # 按延期天数排序
        report["tasks"].sort(key=lambda x: x["delay_days"], reverse=True)

        return report