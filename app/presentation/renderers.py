"""
PM Digital Employee - Result Renderers
项目经理数字员工系统 - 结果渲染器

将Skill执行结果渲染为飞书可展示的格式。
飞书作为唯一用户交互入口。
"""

from typing import Any, Dict, List, Optional

from app.orchestrator.schemas import SkillExecutionResult
from app.presentation.cards import create_card


class ResultRenderer:
    """
    结果渲染器.

    将Skill执行结果渲染为飞书消息格式。
    """

    def render(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """
        渲染执行结果.

        Args:
            result: 执行结果

        Returns:
            Dict: 渲染后的消息数据
        """
        if not result.success:
            return self._render_error(result)

        presentation_type = result.presentation_type

        if presentation_type == "text":
            return self._render_text(result)

        if presentation_type == "card":
            return self._render_card(result)

        if presentation_type == "table":
            return self._render_table(result)

        if presentation_type == "file":
            return self._render_file(result)

        # 默认文本
        return self._render_text(result)

    def _render_text(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染文本结果."""
        data = result.presentation_data or {}
        text = data.get("text", "")

        return {
            "msg_type": "text",
            "content": text,
        }

    def _render_card(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染卡片结果."""
        data = result.presentation_data or {}

        # 如果已有卡片内容，直接使用
        if "card" in data:
            return {
                "msg_type": "interactive",
                "card": data["card"],
            }

        # 根据Skill类型选择卡片模板
        skill_name = result.skill_name
        card_type = self._get_card_type(skill_name)

        try:
            card = create_card(card_type, **data)
            return {
                "msg_type": "interactive",
                "card": card,
            }
        except ValueError:
            # 未知卡片类型，使用默认卡片
            return self._render_default_card(result)

    def _render_table(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染表格结果."""
        data = result.presentation_data or {}
        columns = data.get("columns", [])
        rows = data.get("rows", [])

        if columns and rows:
            # 转换为Markdown表格
            header_line = "| " + " | ".join(columns) + " |"
            separator_line = "| " + " | ".join(["---"] * len(columns)) + " |"

            data_lines = []
            for row in rows:
                row_values = [str(row.get(col, "")) for col in columns]
                data_lines.append("| " + " | ".join(row_values) + " |")

            table_markdown = header_line + "\n" + separator_line + "\n" + "\n".join(data_lines)

            # 返回文本格式
            return {
                "msg_type": "text",
                "content": table_markdown,
            }

        return self._render_text(result)

    def _render_file(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染文件结果."""
        data = result.presentation_data or {}

        return {
            "msg_type": "file",
            "file_key": data.get("file_key", ""),
            "file_name": data.get("file_name", ""),
            "file_type": data.get("file_type", "docx"),
        }

    def _render_error(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染错误结果."""
        error_message = result.error_message or "执行失败"

        card = create_card(
            "error",
            error_message=error_message,
        )

        return {
            "msg_type": "interactive",
            "card": card,
        }

    def _render_default_card(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """渲染默认卡片."""
        data = result.presentation_data or {}

        card = create_card(
            "success",
            title=result.skill_name,
            message=data.get("text", "执行成功"),
        )

        return {
            "msg_type": "interactive",
            "card": card,
        }

    def _get_card_type(
        self,
        skill_name: str,
    ) -> str:
        """根据Skill名称获取卡片类型."""
        mapping = {
            "project_overview": "project_overview",
            "risk_alert": "risk_alert",
            "weekly_report": "weekly_report",
            "task_update": "task_update",
            "clarification": "clarification",
        }
        return mapping.get(skill_name, "success")


class ProjectDataRenderer(ResultRenderer):
    """
    项目数据渲染器.

    专门渲染项目相关数据。
    """

    def render_project_list(
        self,
        projects: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """渲染项目列表."""
        if not projects:
            return {
                "msg_type": "text",
                "content": "暂无项目",
            }

        text = "## 项目列表\n\n"
        for p in projects:
            status_icon = {"active": "🟢", "completed": "✅", "paused": "⏸️"}.get(
                p.get("status", "active"), "⚪"
            )
            text += f"{status_icon} **{p.get('name', '')}** - {p.get('status', '')}\n"

        return {
            "msg_type": "text",
            "content": text,
        }

    def render_task_list(
        self,
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """渲染任务列表."""
        if not tasks:
            return {
                "msg_type": "text",
                "content": "暂无任务",
            }

        text = "## 任务列表\n\n"
        for t in tasks:
            status_icon = {
                "completed": "✅",
                "in_progress": "⏳",
                "pending": "⏸️",
                "blocked": "🚫",
            }.get(t.get("status", "pending"), "⚪")
            progress = t.get("progress", 0)
            text += f"{status_icon} {t.get('name', '')} - {progress}%\n"

        return {
            "msg_type": "text",
            "content": text,
        }

    def render_milestone_timeline(
        self,
        milestones: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """渲染里程碑时间线."""
        if not milestones:
            return {
                "msg_type": "text",
                "content": "暂无里程碑",
            }

        text = "## 里程碑\n\n"
        for m in milestones:
            status_icon = "✅" if m.get("status") == "completed" else "⏳"
            text += f"{status_icon} **{m.get('name', '')}**\n"
            text += f"   截止: {m.get('due_date', '')}\n\n"

        return {
            "msg_type": "text",
            "content": text,
        }


class ReportRenderer(ResultRenderer):
    """
    报告渲染器.

    专门渲染各类报告。
    """

    def render_weekly_report(
        self,
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """渲染周报."""
        card = create_card(
            "weekly_report",
            project_name=report_data.get("project_name", ""),
            week_start=report_data.get("week_start", ""),
            week_end=report_data.get("week_end", ""),
            report_content=report_data.get("report_content", ""),
        )

        return {
            "msg_type": "interactive",
            "card": card,
        }

    def render_wbs(
        self,
        wbs_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """渲染WBS."""
        text = f"## WBS - {wbs_data.get('project_name', '')}\n\n"
        text += wbs_data.get("wbs_content", "")

        return {
            "msg_type": "text",
            "content": text,
        }


# 全局渲染器实例
_result_renderer: Optional[ResultRenderer] = None
_project_renderer: Optional[ProjectDataRenderer] = None
_report_renderer: Optional[ReportRenderer] = None


def get_result_renderer() -> ResultRenderer:
    """获取结果渲染器."""
    global _result_renderer
    if _result_renderer is None:
        _result_renderer = ResultRenderer()
    return _result_renderer


def get_project_renderer() -> ProjectDataRenderer:
    """获取项目渲染器."""
    global _project_renderer
    if _project_renderer is None:
        _project_renderer = ProjectDataRenderer()
    return _project_renderer


def get_report_renderer() -> ReportRenderer:
    """获取报告渲染器."""
    global _report_renderer
    if _report_renderer is None:
        _report_renderer = ReportRenderer()
    return _report_renderer