"""
PM Digital Employee - Task Update Skill
项目经理数字员工系统 - 任务进度更新Skill

更新任务进度状态，包括完成百分比、状态变更、备注添加。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orchestrator.schemas import SkillExecutionContext, SkillExecutionResult, SkillManifest
from app.orchestrator.skill_manifest import get_task_update_manifest
from app.skills.base import BaseSkill


class TaskUpdateSkill(BaseSkill):
    """
    任务进度更新Skill.

    更新任务进度状态。
    """

    skill_name = "task_update"
    display_name = "任务进度更新"
    description = "更新任务进度状态，包括完成百分比、状态变更、备注添加。用户可以输入'更新任务进度'、'完成任务'、'任务状态'等触发。"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行Skill."""
        # 获取参数
        task_id = self.get_param("task_id")
        progress = self.get_param("progress")
        status = self.get_param("status")
        notes = self.get_param("notes", "")

        if not task_id:
            return self.build_error_result("请提供任务ID或任务名称")

        # 验证进度值
        if progress is not None:
            try:
                progress = int(progress)
                if progress < 0 or progress > 100:
                    return self.build_error_result("进度值应在0-100之间")
            except ValueError:
                return self.build_error_result("进度值应为数字")

        # 验证状态值
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        if status and status not in valid_statuses:
            return self.build_error_result(f"状态值应为: {', '.join(valid_statuses)}")

        # 更新任务
        result = await self._update_task(task_id, progress, status, notes)

        return self.build_success_result(
            output=result,
            presentation_type="text",
            presentation_data={
                "text": f"✅ 任务 **{result.get('task_name', task_id)}** 已更新\n\n"
                f"- 进度: {result.get('progress', 0)}%\n"
                f"- 状态: {result.get('status', '未知')}\n"
                f"- 备注: {result.get('notes', '无')}",
            },
        )

    async def _update_task(
        self,
        task_id: str,
        progress: Optional[int],
        status: Optional[str],
        notes: str,
    ) -> Dict[str, Any]:
        """
        更新任务.

        Args:
            task_id: 任务ID
            progress: 进度
            status: 状态
            notes: 备注

        Returns:
            Dict: 更新结果
        """
        if not self._session:
            # 返回模拟结果
            return {
                "task_id": task_id,
                "task_name": f"任务_{task_id}",
                "progress": progress or 0,
                "status": status or "in_progress",
                "notes": notes,
            }

        from app.domain.models.task import Task

        # 尝试解析UUID
        try:
            task_uuid = uuid.UUID(task_id)
        except ValueError:
            # 可能是任务名称，需要查询
            result = await self._session.execute(
                select(Task).where(Task.name == task_id),
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValueError(f"未找到任务: {task_id}")

            task_uuid = task.id

        # 查询任务
        result = await self._session.execute(
            select(Task).where(Task.id == task_uuid),
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 更新字段
        if progress is not None:
            task.progress = progress

        if status:
            task.status = status

        if notes:
            task.notes = notes

        await self._session.commit()

        return {
            "task_id": str(task.id),
            "task_name": task.name,
            "progress": task.progress or 0,
            "status": task.status.value if task.status else "unknown",
            "notes": task.notes or "",
        }

    @classmethod
    def get_manifest(cls) -> SkillManifest:
        """获取Skill Manifest."""
        return get_task_update_manifest()