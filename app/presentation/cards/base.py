"""
PM Digital Employee - Card Base
项目经理数字员工系统 - 飞书卡片基类

定义飞书卡片的基础结构和构建方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.integrations.lark.schemas import LarkCardBuilder


class BaseCard(ABC):
    """
    飞书卡片基类.

    所有具体卡片必须继承此基类。
    """

    def __init__(self) -> None:
        """初始化卡片."""
        self._builder = LarkCardBuilder()

    @abstractmethod
    def build(self, **kwargs) -> Dict[str, Any]:
        """
        构建卡片.

        Args:
            **kwargs: 卡片参数

        Returns:
            Dict: 卡片JSON
        """
        pass

    def _add_header(
        self,
        title: str,
        color: str = "blue",
    ) -> None:
        """添加标题."""
        self._builder.set_header(title, color)

    def _add_markdown(
        self,
        content: str,
    ) -> None:
        """添加Markdown内容."""
        self._builder.add_markdown(content)

    def _add_divider(self) -> None:
        """添加分割线."""
        self._builder.add_divider()

    def _add_fields(
        self,
        fields: List[Dict[str, str]],
    ) -> None:
        """添加字段列表."""
        self._builder.add_field(fields)

    def _add_actions(
        self,
        actions: List[Dict[str, Any]],
    ) -> None:
        """添加操作按钮."""
        self._builder.add_action(actions)

    @staticmethod
    def create_button(
        text: str,
        value: Dict[str, Any],
        style: str = "primary",
    ) -> Dict[str, Any]:
        """
        创建按钮.

        Args:
            text: 按钮文本
            value: 按钮值
            style: 样式

        Returns:
            Dict: 按钮元素
        """
        return LarkCardBuilder.create_button(text, value, style)


class ProjectOverviewCard(BaseCard):
    """
    项目总览卡片.
    """

    def build(
        self,
        project_name: str,
        status: str,
        progress: int,
        pm_name: str,
        start_date: str = "",
        end_date: str = "",
        milestones: Optional[List[Dict]] = None,
        risks: Optional[List[Dict]] = None,
        cost_summary: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建项目总览卡片."""
        self._add_header(f"项目总览：{project_name}", "blue")

        # 基本信息
        self._add_fields([
            {"content": f"**项目状态**: {status}"},
            {"content": f"**整体进度**: {progress}%"},
            {"content": f"**项目经理**: {pm_name}"},
            {"content": f"**起止日期**: {start_date} - {end_date}"},
        ])

        self._add_divider()

        # 里程碑
        if milestones:
            milestone_text = "**里程碑状态**\n\n"
            for m in milestones[:5]:
                status_icon = "✅" if m.get("status") == "completed" else "⏳"
                milestone_text += f"{status_icon} {m.get('name', '')}: {m.get('due_date', '')}\n"
            self._add_markdown(milestone_text)
            self._add_divider()

        # 风险
        if risks:
            risk_text = "**风险预警**\n\n"
            for r in risks[:3]:
                level_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    r.get("level", "low"), "⚪"
                )
                risk_text += f"{level_icon} {r.get('description', '')}\n"
            self._add_markdown(risk_text)
            self._add_divider()

        # 成本
        if cost_summary:
            cost_text = f"**成本概览**\n\n"
            cost_text += f"- 预算: ¥{cost_summary.get('budget', 0):,.0f}\n"
            cost_text += f"- 实际: ¥{cost_summary.get('actual', 0):,.0f}\n"
            variance = cost_summary.get('variance', 0)
            variance_percent = cost_summary.get('variance_percent', 0)
            cost_text += f"- 偏差: ¥{variance:,.0f} ({variance_percent:.1f}%)\n"
            self._add_markdown(cost_text)

        return self._builder.build()


class RiskAlertCard(BaseCard):
    """
    风险预警卡片.
    """

    def build(
        self,
        project_name: str,
        risks: List[Dict],
        **kwargs,
    ) -> Dict[str, Any]:
        """构建风险预警卡片."""
        # 根据最高风险等级设置颜色
        high_risks = [r for r in risks if r.get("level") == "high"]
        color = "red" if high_risks else "yellow" if risks else "green"

        self._add_header(f"风险预警：{project_name}", color)

        if not risks:
            self._add_markdown("✅ 当前无风险项")
        else:
            # 高风险
            if high_risks:
                self._add_markdown("### 🔴 高风险")
                for r in high_risks:
                    self._add_markdown(
                        f"- **{r.get('description', '')}**\n"
                        f"  影响: {r.get('impact', '')} | 应对: {r.get('mitigation', '')}"
                    )
                self._add_divider()

            # 中风险
            medium_risks = [r for r in risks if r.get("level") == "medium"]
            if medium_risks:
                self._add_markdown("### 🟡 中风险")
                for r in medium_risks:
                    self._add_markdown(f"- {r.get('description', '')}")
                self._add_divider()

            # 低风险
            low_risks = [r for r in risks if r.get("level") == "low"]
            if low_risks:
                self._add_markdown(f"### 🟢 低风险\n共 {len(low_risks)} 项")

        return self._builder.build()


class WeeklyReportCard(BaseCard):
    """
    周报卡片.
    """

    def build(
        self,
        project_name: str,
        week_start: str,
        week_end: str,
        report_content: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建周报卡片."""
        self._add_header(f"项目周报：{project_name}", "blue")

        self._add_markdown(f"**报告周期**: {week_start} - {week_end}")
        self._add_divider()
        self._add_markdown(report_content)

        # 添加导出按钮
        self._add_divider()
        self._add_actions([
            self.create_button(
                "导出Word",
                {"action": "export_word", "report_type": "weekly"},
                "primary",
            ),
            self.create_button(
                "发送邮件",
                {"action": "send_email"},
                "default",
            ),
        ])

        return self._builder.build()


class ClarificationCard(BaseCard):
    """
    意图澄清卡片.
    """

    def build(
        self,
        matched_skill: str,
        skill_description: str,
        confidence: float,
        alternatives: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建澄清卡片."""
        self._add_header("请确认您的意图", "blue")

        self._add_markdown(
            f"检测到您可能想要：**{skill_description}**\n\n"
            f"置信度: {confidence:.0%}"
        )

        if alternatives:
            self._add_divider()
            alt_text = "其他可能的意图：\n"
            for alt in alternatives[:3]:
                alt_text += f"- {alt.get('description', '')}\n"
            self._add_markdown(alt_text)

        self._add_divider()

        # 确认/取消按钮
        self._add_actions([
            self.create_button(
                "确认执行",
                {"action": "confirm", "skill": matched_skill},
                "primary",
            ),
            self.create_button(
                "取消",
                {"action": "cancel"},
                "default",
            ),
        ])

        return self._builder.build()


class TaskUpdateCard(BaseCard):
    """
    任务更新卡片.
    """

    def build(
        self,
        task_name: str,
        task_id: str,
        current_progress: int,
        current_status: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建任务更新卡片."""
        self._add_header(f"更新任务：{task_name}", "blue")

        self._add_fields([
            {"content": f"**当前进度**: {current_progress}%"},
            {"content": f"**当前状态**: {current_status}"},
        ])

        self._add_divider()
        self._add_markdown("请选择更新内容：")

        # 快捷更新按钮
        self._add_actions([
            self.create_button(
                "完成",
                {"action": "update_task", "task_id": task_id, "progress": 100, "status": "completed"},
                "primary",
            ),
            self.create_button(
                "进行中",
                {"action": "update_task", "task_id": task_id, "status": "in_progress"},
                "default",
            ),
            self.create_button(
                "受阻",
                {"action": "update_task", "task_id": task_id, "status": "blocked"},
                "danger",
            ),
        ])

        return self._builder.build()


class ApprovalStatusCard(BaseCard):
    """
    审批状态卡片.
    """

    def build(
        self,
        approval_id: str,
        approval_type: str,
        status: str,
        requester_name: str,
        created_at: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建审批状态卡片."""
        status_colors = {
            "pending": "yellow",
            "approved": "green",
            "rejected": "red",
        }
        color = status_colors.get(status, "grey")

        status_texts = {
            "pending": "待审批",
            "approved": "已通过",
            "rejected": "已拒绝",
        }
        status_text = status_texts.get(status, status)

        self._add_header(f"审批：{approval_type}", color)

        self._add_fields([
            {"content": f"**审批编号**: {approval_id}"},
            {"content": f"**状态**: {status_text}"},
            {"content": f"**申请人**: {requester_name}"},
            {"content": f"**申请时间**: {created_at}"},
        ])

        if status == "pending":
            self._add_divider()
            self._add_actions([
                self.create_button(
                    "通过",
                    {"action": "approve", "approval_id": approval_id},
                    "primary",
                ),
                self.create_button(
                    "拒绝",
                    {"action": "reject", "approval_id": approval_id},
                    "danger",
                ),
            ])

        return self._builder.build()


class ErrorCard(BaseCard):
    """
    错误提示卡片.
    """

    def build(
        self,
        error_message: str,
        retry_action: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建错误卡片."""
        self._add_header("操作失败", "red")

        self._add_markdown(f"❌ {error_message}")

        if retry_action:
            self._add_divider()
            self._add_actions([
                self.create_button(
                    "重试",
                    retry_action,
                    "primary",
                ),
            ])

        return self._builder.build()


class SuccessCard(BaseCard):
    """
    成功提示卡片.
    """

    def build(
        self,
        title: str,
        message: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """构建成功卡片."""
        self._add_header(title, "green")

        self._add_markdown(f"✅ {message}")

        return self._builder.build()


# 卡片工厂
CARD_CLASSES = {
    "project_overview": ProjectOverviewCard,
    "risk_alert": RiskAlertCard,
    "weekly_report": WeeklyReportCard,
    "clarification": ClarificationCard,
    "task_update": TaskUpdateCard,
    "approval_status": ApprovalStatusCard,
    "error": ErrorCard,
    "success": SuccessCard,
}


def create_card(card_type: str, **kwargs) -> Dict[str, Any]:
    """
    创建卡片.

    Args:
        card_type: 卡片类型
        **kwargs: 卡片参数

    Returns:
        Dict: 卡片JSON
    """
    card_class = CARD_CLASSES.get(card_type)

    if card_class is None:
        raise ValueError(f"Unknown card type: {card_type}")

    card = card_class()
    return card.build(**kwargs)