"""
PM Digital Employee - Notification Service
项目经理数字员工系统 - 任务通知服务

v1.2.0新增：提供任务分配、状态变更、延期预警等通知功能。

主要功能：
1. send_task_assignment_notification - 任务分配通知
2. send_task_status_change_notification - 状态变更通知
3. send_task_delay_warning - 延期预警通知
"""

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import TaskNotFoundError
from app.domain.enums import TaskStatus
from app.domain.models.task import Task

logger = get_logger(__name__)


class NotificationType:
    """通知类型枚举."""

    TASK_ASSIGNMENT = "task_assignment"         # 任务分配通知
    TASK_STATUS_CHANGE = "task_status_change"   # 状态变更通知
    TASK_DELAY_WARNING = "task_delay_warning"   # 延期预警通知
    TASK_COMPLETION = "task_completion"         # 任务完成通知
    TASK_PROGRESS_UPDATE = "task_progress_update"  # 进度更新通知


class NotificationService:
    """
    任务通知服务.

    提供任务相关的通知发送功能，支持飞书消息推送。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化通知服务.

        Args:
            session: 数据库会话
        """
        self.session = session
        self._lark_service: Optional[Any] = None

    def _get_lark_service(self) -> Any:
        """
        获取飞书服务实例.

        Returns:
            LarkService: 飞书服务实例
        """
        if self._lark_service is None:
            from app.integrations.lark.service import get_lark_service
            self._lark_service = get_lark_service()
        return self._lark_service

    # ==================== 任务分配通知 ====================

    async def send_task_assignment_notification(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        assigned_by_id: Optional[str] = None,
        assigned_by_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送任务分配通知.

        当任务被分配给某人时，通知该人员。

        Args:
            task_id: 任务ID
            project_id: 项目ID
            assigned_by_id: 分派人飞书用户ID
            assigned_by_name: 分派人姓名

        Returns:
            Dict: 通知发送结果
        """
        # 获取任务信息
        task = await self._get_task(task_id, project_id)

        if not task.assignee_id:
            logger.warning(f"Task {task_id} has no assignee, skipping notification")
            return {"status": "skipped", "reason": "no_assignee"}

        # 构建通知内容
        notification_data = self._build_assignment_notification(
            task, assigned_by_id, assigned_by_name
        )

        # 发送飞书消息
        result = await self._send_lark_message(
            user_id=task.assignee_id,
            message_type=NotificationType.TASK_ASSIGNMENT,
            message_data=notification_data,
        )

        logger.info(
            "Task assignment notification sent",
            extra={
                "task_id": str(task_id),
                "assignee_id": task.assignee_id,
                "assigned_by": assigned_by_name,
            }
        )

        return result

    def _build_assignment_notification(
        self,
        task: Task,
        assigned_by_id: Optional[str],
        assigned_by_name: Optional[str],
    ) -> Dict[str, Any]:
        """
        构建任务分配通知内容.

        Args:
            task: 任务对象
            assigned_by_id: 分派人ID
            assigned_by_name: 分派人姓名

        Returns:
            Dict: 通知内容
        """
        # 格式化日期
        start_date_str = str(task.start_date) if task.start_date else "待定"
        end_date_str = str(task.end_date) if task.end_date else "待定"

        # 构建飞书卡片消息
        card_content = {
            "type": "template",
            "data": {
                "template_id": "task_assignment_card",
                "template_variable": {
                    "task_name": task.name,
                    "task_code": task.code,
                    "task_description": task.description or "无描述",
                    "priority": task.priority,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "assigned_by": assigned_by_name or "系统",
                    "estimated_hours": str(task.estimated_hours) if task.estimated_hours else "待定",
                    "deliverable": task.deliverable or "无",
                },
            },
        }

        return {
            "card": card_content,
            "text": f"【任务分配】您被分配了新任务：{task.name}",
            "task_id": str(task.id),
            "project_id": str(task.project_id),
            "assignee_id": task.assignee_id,
        }

    # ==================== 状态变更通知 ====================

    async def send_task_status_change_notification(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        old_status: TaskStatus,
        new_status: TaskStatus,
        changed_by_id: Optional[str] = None,
        changed_by_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送任务状态变更通知.

        当任务状态发生重要变更时（如完成、延期），通知相关人员。

        Args:
            task_id: 任务ID
            project_id: 项目ID
            old_status: 原状态
            new_status: 新状态
            changed_by_id: 变更人飞书用户ID
            changed_by_name: 变更人姓名

        Returns:
            Dict: 通知发送结果
        """
        # 获取任务信息
        task = await self._get_task(task_id, project_id)

        # 确定需要通知的人员
        notify_users = await self._get_notify_users_for_status_change(task)

        if not notify_users:
            logger.warning(f"No users to notify for task {task_id} status change")
            return {"status": "skipped", "reason": "no_notify_users"}

        # 构建通知内容
        notification_data = self._build_status_change_notification(
            task, old_status, new_status, changed_by_id, changed_by_name
        )

        # 发送飞书消息给所有相关人员
        results = []
        for user_id in notify_users:
            result = await self._send_lark_message(
                user_id=user_id,
                message_type=NotificationType.TASK_STATUS_CHANGE,
                message_data=notification_data,
            )
            results.append(result)

        logger.info(
            "Task status change notification sent",
            extra={
                "task_id": str(task_id),
                "old_status": old_status,
                "new_status": new_status,
                "notify_count": len(notify_users),
            }
        )

        return {
            "status": "success",
            "notify_count": len(notify_users),
            "results": results,
        }

    def _build_status_change_notification(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        changed_by_id: Optional[str],
        changed_by_name: Optional[str],
    ) -> Dict[str, Any]:
        """
        构建状态变更通知内容.

        Args:
            task: 任务对象
            old_status: 原状态
            new_status: 新状态
            changed_by_id: 变更人ID
            changed_by_name: 变更人姓名

        Returns:
            Dict: 通知内容
        """
        # 状态中文名映射
        status_names = {
            TaskStatus.PENDING: "待开始",
            TaskStatus.IN_PROGRESS: "进行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.DELAYED: "已延期",
            TaskStatus.CANCELLED: "已取消",
            TaskStatus.BLOCKED: "被阻塞",
        }

        old_status_name = status_names.get(old_status, old_status)
        new_status_name = status_names.get(new_status, new_status)

        # 根据新状态选择不同的通知标题
        if new_status == TaskStatus.COMPLETED:
            title = "【任务完成】"
            highlight_color = "green"
        elif new_status == TaskStatus.DELAYED:
            title = "【任务延期】"
            highlight_color = "red"
        elif new_status == TaskStatus.BLOCKED:
            title = "【任务阻塞】"
            highlight_color = "orange"
        else:
            title = "【状态变更】"
            highlight_color = "blue"

        # 构建飞书卡片消息
        card_content = {
            "type": "template",
            "data": {
                "template_id": "task_status_change_card",
                "template_variable": {
                    "title": title,
                    "task_name": task.name,
                    "task_code": task.code,
                    "old_status": old_status_name,
                    "new_status": new_status_name,
                    "changed_by": changed_by_name or "系统",
                    "progress": str(task.progress),
                    "highlight_color": highlight_color,
                    "actual_end_date": str(task.actual_end_date) if task.actual_end_date else None,
                },
            },
        }

        return {
            "card": card_content,
            "text": f"{title}任务 '{task.name}' 状态从 '{old_status_name}' 变更为 '{new_status_name}'",
            "task_id": str(task.id),
            "project_id": str(task.project_id),
        }

    async def _get_notify_users_for_status_change(
        self,
        task: Task,
    ) -> List[str]:
        """
        获取状态变更需要通知的用户列表.

        Args:
            task: 任务对象

        Returns:
            List[str]: 需要通知的用户ID列表
        """
        notify_users = []

        # 负责人
        if task.assignee_id:
            notify_users.append(task.assignee_id)

        # 如果任务完成或延期，还需要通知项目经理
        # 这需要从项目关联中获取项目经理ID
        # 暂时简化处理，只通知负责人

        return notify_users

    # ==================== 延期预警通知 ====================

    async def send_task_delay_warning(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        delay_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        发送任务延期预警通知.

        当检测到任务延期时，发送预警通知给相关人员。

        Args:
            task_id: 任务ID
            project_id: 项目ID
            delay_days: 延期天数（可选，不传则自动计算）

        Returns:
            Dict: 通知发送结果
        """
        # 获取任务信息
        task = await self._get_task(task_id, project_id)

        # 计算延期天数
        if delay_days is None:
            delay_days = task.get_delay_days()

        if delay_days <= 0:
            logger.warning(f"Task {task_id} is not delayed, skipping warning notification")
            return {"status": "skipped", "reason": "not_delayed"}

        # 确定需要通知的人员
        notify_users = await self._get_notify_users_for_delay_warning(task)

        if not notify_users:
            logger.warning(f"No users to notify for task {task_id} delay warning")
            return {"status": "skipped", "reason": "no_notify_users"}

        # 构建通知内容
        notification_data = self._build_delay_warning_notification(task, delay_days)

        # 发送飞书消息给所有相关人员
        results = []
        for user_id in notify_users:
            result = await self._send_lark_message(
                user_id=user_id,
                message_type=NotificationType.TASK_DELAY_WARNING,
                message_data=notification_data,
            )
            results.append(result)

        logger.warning(
            "Task delay warning notification sent",
            extra={
                "task_id": str(task_id),
                "delay_days": delay_days,
                "notify_count": len(notify_users),
            }
        )

        return {
            "status": "success",
            "delay_days": delay_days,
            "notify_count": len(notify_users),
            "results": results,
        }

    def _build_delay_warning_notification(
        self,
        task: Task,
        delay_days: int,
    ) -> Dict[str, Any]:
        """
        构建延期预警通知内容.

        Args:
            task: 任务对象
            delay_days: 延期天数

        Returns:
            Dict: 通知内容
        """
        # 根据延期天数确定预警等级
        if delay_days >= 14:
            severity = "严重延期"
            severity_color = "red"
        elif delay_days >= 7:
            severity = "中度延期"
            severity_color = "orange"
        else:
            severity = "轻度延期"
            severity_color = "yellow"

        # 构建飞书卡片消息
        card_content = {
            "type": "template",
            "data": {
                "template_id": "task_delay_warning_card",
                "template_variable": {
                    "task_name": task.name,
                    "task_code": task.code,
                    "delay_days": str(delay_days),
                    "severity": severity,
                    "severity_color": severity_color,
                    "planned_end_date": str(task.end_date) if task.end_date else "未设置",
                    "current_progress": str(task.progress),
                    "assignee_name": task.assignee_name or "未分配",
                    "recommendation": self._get_delay_recommendation(delay_days),
                },
            },
        }

        return {
            "card": card_content,
            "text": f"【延期预警】任务 '{task.name}' 已延期 {delay_days} 天，请及时处理！",
            "task_id": str(task.id),
            "project_id": str(task.project_id),
            "delay_days": delay_days,
        }

    def _get_delay_recommendation(
        self,
        delay_days: int,
    ) -> str:
        """
        获取延期处理建议.

        Args:
            delay_days: 延期天数

        Returns:
            str: 处理建议
        """
        if delay_days >= 14:
            return "建议立即召开项目会议，评估项目整体进度，调整项目计划或申请延期。"
        elif delay_days >= 7:
            return "建议及时分析延期原因，评估对后续任务的影响，协调资源推进。"
        else:
            return "建议关注任务进度，评估是否需要调整优先级或请求协助。"

    async def _get_notify_users_for_delay_warning(
        self,
        task: Task,
    ) -> List[str]:
        """
        获取延期预警需要通知的用户列表.

        Args:
            task: 任务对象

        Returns:
            List[str]: 需要通知的用户ID列表
        """
        notify_users = []

        # 负责人
        if task.assignee_id:
            notify_users.append(task.assignee_id)

        # 延期预警应该通知项目经理
        # 从项目关联获取项目经理
        from app.domain.models.project import Project
        result = await self.session.execute(
            select(Project).where(Project.id == task.project_id)
        )
        project = result.scalar_one_or_none()

        if project and project.pm_id:
            if project.pm_id not in notify_users:
                notify_users.append(project.pm_id)

        return notify_users

    # ==================== 批量延期预警 ====================

    async def send_batch_delay_warnings(
        self,
        project_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        批量发送项目延期预警通知.

        检查项目中所有延期任务，并发送预警通知。

        Args:
            project_id: 项目ID

        Returns:
            Dict: 批量发送结果
        """
        from app.services.task_service import TaskService

        task_service = TaskService(self.session)
        delayed_tasks = await task_service.detect_delayed_tasks(project_id)

        results = []
        for task in delayed_tasks:
            try:
                result = await self.send_task_delay_warning(task.id, project_id)
                results.append({
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "result": result,
                })
            except Exception as e:
                logger.error(f"Failed to send delay warning for task {task.id}: {e}")
                results.append({
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "result": {"status": "failed", "error": str(e)},
                })

        logger.info(
            "Batch delay warnings sent",
            extra={
                "project_id": str(project_id),
                "delayed_tasks_count": len(delayed_tasks),
            }
        )

        return {
            "project_id": str(project_id),
            "total_delayed": len(delayed_tasks),
            "notifications_sent": len([r for r in results if r["result"]["status"] == "success"]),
            "results": results,
        }

    # ==================== 任务完成通知 ====================

    async def send_task_completion_notification(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
        completed_by_id: Optional[str] = None,
        completed_by_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送任务完成通知.

        当任务完成时，通知相关人员。

        Args:
            task_id: 任务ID
            project_id: 项目ID
            completed_by_id: 完成人飞书用户ID
            completed_by_name: 完成人姓名

        Returns:
            Dict: 通知发送结果
        """
        return await self.send_task_status_change_notification(
            task_id=task_id,
            project_id=project_id,
            old_status=TaskStatus.IN_PROGRESS,
            new_status=TaskStatus.COMPLETED,
            changed_by_id=completed_by_id,
            changed_by_name=completed_by_name,
        )

    # ==================== 辅助方法 ====================

    async def _get_task(
        self,
        task_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Task:
        """
        获取任务信息.

        Args:
            task_id: 任务ID
            project_id: 项目ID

        Returns:
            Task: 任务对象

        Raises:
            TaskNotFoundError: 任务不存在
        """
        result = await self.session.execute(
            select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.project_id == project_id,
                )
            )
        )
        task = result.scalar_one_or_none()

        if not task:
            raise TaskNotFoundError(task_id=str(task_id))

        return task

    async def _send_lark_message(
        self,
        user_id: str,
        message_type: str,
        message_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        发送飞书消息.

        Args:
            user_id: 飞书用户ID
            message_type: 消息类型
            message_data: 消息内容

        Returns:
            Dict: 发送结果
        """
        try:
            lark_service = self._get_lark_service()

            # 发送飞书消息卡片
            # 注意：这里需要根据实际的飞书API进行实现
            await lark_service.send_message(
                receive_id=user_id,
                receive_id_type="open_id",
                msg_type="interactive",
                content=message_data.get("card"),
            )

            return {
                "status": "success",
                "user_id": user_id,
                "message_type": message_type,
            }

        except Exception as e:
            logger.error(f"Failed to send lark message to {user_id}: {e}")
            return {
                "status": "failed",
                "user_id": user_id,
                "error": str(e),
            }