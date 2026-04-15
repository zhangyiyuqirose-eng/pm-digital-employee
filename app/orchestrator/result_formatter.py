"""
PM Digital Employee - Result Formatter
PM Digital Employee System - Result formatter

Converts skill execution results to Lark-displayable formats (text, cards, files).
Lark as the primary user interaction entrypoint.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.lark.schemas import LarkCardBuilder
from app.orchestrator.schemas import SkillExecutionResult, SkillManifest

logger = get_logger(__name__)


class ResultFormatter:
    """
    Result formatter.

    Converts skill execution results to Lark display formats.
    """

    def __init__(self) -> None:
        """Initialize formatter."""
        self._max_text_length = 20000  # Lark text message max length
        self._max_card_elements = 50  # Lark card max elements

    def format_result(
        self,
        result: SkillExecutionResult,
        manifest: Optional[SkillManifest] = None,
    ) -> Dict[str, Any]:
        """
        格式化执行结果.

        Args:
            result: Skill执行结果
            manifest: Skill Manifest

        Returns:
            Dict: 格式化后的展示数据
        """
        if not result.success:
            return self._format_error_result(result)

        presentation_type = result.presentation_type

        if presentation_type == "text":
            return self._format_text_result(result)

        if presentation_type == "card":
            return self._format_card_result(result, manifest)

        if presentation_type == "file":
            return self._format_file_result(result)

        if presentation_type == "table":
            return self._format_table_result(result)

        # 默认文本格式
        return self._format_text_result(result)

    def _format_error_result(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """
        格式化错误结果.

        Args:
            result: 执行结果

        Returns:
            Dict: 错误展示数据
        """
        error_message = result.error_message or "Execution failed."

        # Build error card
        card = (
            LarkCardBuilder()
            .set_header("Operation Failed", "red")
            .add_markdown(f"{error_message}")
            .add_divider()
            .add_action(
                [
                    LarkCardBuilder.create_button(
                        "Retry",
                        {"action": "retry", "skill": result.skill_name},
                        "primary",
                    ),
                    LarkCardBuilder.create_button(
                        "Cancel",
                        {"action": "cancel"},
                        "default",
                    ),
                ],
            )
            .build()
        )

        return {
            "type": "card",
            "content": card,
        }

    def _format_text_result(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """
        格式化文本结果.

        Args:
            result: 执行结果

        Returns:
            Dict: 文本展示数据
        """
        data = result.presentation_data or {}
        text = data.get("text", "")

        # 截断过长文本
        if len(text) > self._max_text_length:
            text = text[:self._max_text_length - 50] + "..."

        # 添加Skill名称标识
        if result.skill_name:
            text = f"【{result.skill_name}】\n\n{text}"

        return {
            "type": "text",
            "content": text,
        }

    def _format_card_result(
        self,
        result: SkillExecutionResult,
        manifest: Optional[SkillManifest],
    ) -> Dict[str, Any]:
        """
        格式化卡片结果.

        Args:
            result: 执行结果
            manifest: Skill Manifest

        Returns:
            Dict: 卡片展示数据
        """
        data = result.presentation_data or {}

        # 如果已有卡片数据，直接使用
        if "card" in data:
            return {
                "type": "card",
                "content": data["card"],
            }

        # 根据数据构建卡片
        builder = LarkCardBuilder()

        # 设置标题
        title = data.get("title", manifest.display_name if manifest else "执行结果")
        template = data.get("template", "blue")
        builder.set_header(title, template)

        # 添加内容
        if "summary" in data:
            builder.add_markdown(data["summary"])

        if "sections" in data:
            for section in data["sections"][:self._max_card_elements]:
                builder.add_markdown(section)

        if "fields" in data:
            fields = [
                {"content": f"{k}: {v}"}
                for k, v in data["fields"].items()
            ]
            builder.add_field(fields)

        if "actions" in data:
            builder.add_action(data["actions"])

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def _format_file_result(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """
        格式化文件结果.

        Args:
            result: 执行结果

        Returns:
            Dict: 文件展示数据
        """
        data = result.presentation_data or {}

        return {
            "type": "file",
            "file_key": data.get("file_key", ""),
            "file_name": data.get("file_name", ""),
            "file_type": data.get("file_type", "docx"),
            "download_url": data.get("download_url", ""),
        }

    def _format_table_result(
        self,
        result: SkillExecutionResult,
    ) -> Dict[str, Any]:
        """
        格式化表格结果.

        Args:
            result: 执行结果

        Returns:
            Dict: 表格展示数据
        """
        data = result.presentation_data or {}
        columns = data.get("columns", [])
        rows = data.get("rows", [])

        # 将表格转换为Markdown
        if columns and rows:
            # 表头
            header_line = "| " + " | ".join(columns) + " |"
            separator_line = "| " + " | ".join(["---"] * len(columns)) + " |"

            # 数据行
            data_lines = []
            for row in rows:
                row_values = [str(row.get(col, "")) for col in columns]
                data_lines.append("| " + " | ".join(row_values) + " |")

            table_markdown = header_line + "\n" + separator_line + "\n" + "\n".join(data_lines)

            # 构建卡片
            card = (
                LarkCardBuilder()
                .set_header(data.get("title", "数据表格"), "blue")
                .add_markdown(table_markdown)
                .build()
            )

            return {
                "type": "card",
                "content": card,
            }

        return self._format_text_result(result)

    def format_project_overview(
        self,
        project_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        格式化项目总览.

        Args:
            project_data: 项目数据

        Returns:
            Dict: 格式化数据
        """
        builder = LarkCardBuilder()
        builder.set_header(
            f"项目总览：{project_data.get('project_name', '未知项目')}",
            "blue",
        )

        # 基本信息字段
        fields = [
            {"content": f"**项目状态**: {project_data.get('status', '未知')}"},
            {"content": f"**整体进度**: {project_data.get('progress', 0)}%"},
            {"content": f"**项目经理**: {project_data.get('pm_name', '未知')}"},
            {"content": f"**起止日期**: {project_data.get('start_date', '')} - {project_data.get('end_date', '')}"},
        ]
        builder.add_field(fields)

        builder.add_divider()

        # 里程碑摘要
        milestones = project_data.get("milestones", [])
        if milestones:
            milestone_text = "**里程碑状态**\n\n"
            for m in milestones[:5]:
                status_icon = "✅" if m.get("status") == "completed" else "⏳"
                milestone_text += f"{status_icon} {m.get('name', '')}: {m.get('due_date', '')}\n"
            builder.add_markdown(milestone_text)

        builder.add_divider()

        # 风险摘要
        risks = project_data.get("risks", [])
        if risks:
            risk_text = "**风险预警**\n\n"
            for r in risks[:3]:
                level_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    r.get("level", "low"), "⚪",
                )
                risk_text += f"{level_icon} {r.get('description', '')}\n"
            builder.add_markdown(risk_text)

        builder.add_divider()

        # 成本摘要
        cost_data = project_data.get("cost_summary", {})
        if cost_data:
            cost_text = f"**成本概览**\n\n"
            cost_text += f"- 预算: ¥{cost_data.get('budget', 0):,.0f}\n"
            cost_text += f"- 实际支出: ¥{cost_data.get('actual', 0):,.0f}\n"
            cost_text += f"- 偏差: ¥{cost_data.get('variance', 0):,.0f} ({cost_data.get('variance_percent', 0)}%)\n"
            builder.add_markdown(cost_text)

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def format_risk_alert(
        self,
        risks: List[Dict[str, Any]],
        project_name: str,
    ) -> Dict[str, Any]:
        """
        格式化风险预警.

        Args:
            risks: 风险列表
            project_name: 项目名称

        Returns:
            Dict: 格式化数据
        """
        builder = LarkCardBuilder()
        builder.set_header(f"风险预警：{project_name}", "red")

        if not risks:
            builder.add_markdown("✅ 当前无风险项")
        else:
            # 高风险
            high_risks = [r for r in risks if r.get("level") == "high"]
            if high_risks:
                builder.add_markdown("### 🔴 高风险")
                for r in high_risks:
                    builder.add_markdown(
                        f"- **{r.get('description', '')}**\n"
                        f"  影响: {r.get('impact', '')} | 应对: {r.get('mitigation', '')}",
                    )

            builder.add_divider()

            # 中风险
            medium_risks = [r for r in risks if r.get("level") == "medium"]
            if medium_risks:
                builder.add_markdown("### 🟡 中风险")
                for r in medium_risks:
                    builder.add_markdown(f"- {r.get('description', '')}")

            builder.add_divider()

            # 低风险
            low_risks = [r for r in risks if r.get("level") == "low"]
            if low_risks:
                builder.add_markdown("### 🟢 低风险")
                builder.add_markdown(f"共 {len(low_risks)} 项低风险")

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def format_task_update_result(
        self,
        task_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        格式化任务更新结果.

        Args:
            task_data: 任务数据

        Returns:
            Dict: 格式化数据
        """
        builder = LarkCardBuilder()
        builder.set_header("任务更新成功", "green")

        builder.add_markdown(
            f"✅ 任务 **{task_data.get('task_name', '')}** 已更新\n\n"
            f"- 进度: {task_data.get('progress', 0)}%\n"
            f"- 状态: {task_data.get('status', '')}\n"
            f"- 备注: {task_data.get('notes', '')}",
        )

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def format_weekly_report(
        self,
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        格式化周报.

        Args:
            report_data: 周报数据

        Returns:
            Dict: 格式化数据
        """
        builder = LarkCardBuilder()
        builder.set_header(
            f"项目周报：{report_data.get('project_name', '')}",
            "blue",
        )

        # 报告周期
        builder.add_markdown(
            f"**报告周期**: {report_data.get('week_start', '')} - {report_data.get('week_end', '')}",
        )

        builder.add_divider()

        # 本周进展
        builder.add_markdown("### 本周进展")
        completed_tasks = report_data.get("tasks_completed", [])
        for task in completed_tasks:
            builder.add_markdown(f"- ✅ {task.get('name', '')}")

        builder.add_divider()

        # 进行中任务
        builder.add_markdown("### 进行中")
        in_progress_tasks = report_data.get("tasks_in_progress", [])
        for task in in_progress_tasks:
            builder.add_markdown(f"- ⏳ {task.get('name', '')} ({task.get('progress', 0)}%)")

        builder.add_divider()

        # 下周计划
        builder.add_markdown("### 下周计划")
        next_week_tasks = report_data.get("next_week_plan", [])
        for task in next_week_tasks:
            builder.add_markdown(f"- 📋 {task}")

        builder.add_divider()

        # 风险提示
        if report_data.get("risks"):
            builder.add_markdown("### ⚠️ 风险提示")
            builder.add_markdown(report_data.get("risks_summary", ""))

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def format_compliance_review(
        self,
        review_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        格式化合规初审结果.

        Args:
            review_data: 合规检查数据

        Returns:
            Dict: 格式化数据
        """
        status = review_data.get("compliance_status", "")
        template = "green" if status == "passed" else "red"

        builder = LarkCardBuilder()
        builder.set_header(
            f"合规初审：{review_data.get('document_name', '')}",
            template,
        )

        # 检查结果摘要
        passed = review_data.get("passed_count", 0)
        failed = review_data.get("failed_count", 0)
        builder.add_markdown(
            f"**检查结果**: {status}\n\n"
            f"- 通过项: {passed}\n"
            f"- 问题项: {failed}",
        )

        builder.add_divider()

        # 问题详情
        if review_data.get("check_results"):
            builder.add_markdown("### 检查详情")
            for result in review_data.get("check_results", [])[:10]:
                icon = "✅" if result.get("passed") else "❌"
                builder.add_markdown(f"{icon} {result.get('item', '')}")

        builder.add_divider()

        # 缺失项
        missing_items = review_data.get("missing_items", [])
        if missing_items:
            builder.add_markdown("### 缺失项")
            for item in missing_items:
                builder.add_markdown(f"- 🔴 {item}")

        builder.add_divider()

        # 改进建议
        suggestions = review_data.get("suggestions", [])
        if suggestions:
            builder.add_markdown("### 改进建议")
            for suggestion in suggestions:
                builder.add_markdown(f"- {suggestion}")

        card = builder.build()

        return {
            "type": "card",
            "content": card,
        }

    def truncate_text(
        self,
        text: str,
        max_length: Optional[int] = None,
    ) -> str:
        """
        截断文本.

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            str: 截断后的文本
        """
        max_length = max_length or self._max_text_length
        if len(text) <= max_length:
            return text
        return text[:max_length - 50] + "..."


# 全局格式化器实例
_result_formatter: Optional[ResultFormatter] = None


def get_result_formatter() -> ResultFormatter:
    """获取结果格式化器实例."""
    global _result_formatter
    if _result_formatter is None:
        _result_formatter = ResultFormatter()
    return _result_formatter