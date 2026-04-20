"""
PM Digital Employee - Lark Message Sender
项目经理数字员工系统 - 飞书消息发送扩展模块

扩展飞书消息发送能力，支持任务分配、状态变更、延期预警、
成本超支、风险预警等各类业务消息通知。

v1.2.0新增
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.integrations.lark.client import LarkClient, get_lark_client
from app.integrations.lark.schemas import LarkCardBuilder, LarkCardColor

logger = get_logger(__name__)


# ==================== 消息通知构建器 ====================

class LarkMessageSender:
    """
    飞书消息发送扩展模块.

    提供各类业务场景的消息通知发送能力。
    """

    def __init__(self, client: Optional[LarkClient] = None) -> None:
        """
        初始化消息发送器.

        Args:
            client: Lark客户端实例
        """
        self._client = client or get_lark_client()

    # ==================== 任务分配通知 ====================

    async def send_task_assignment_notification(
        self,
        user_id: str,
        task_name: str,
        task_id: str,
        project_name: str,
        assigner_name: str,
        deadline: Optional[str] = None,
        priority: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送任务分配通知.

        Args:
            user_id: 接收者飞书用户ID
            task_name: 任务名称
            task_id: 任务ID
            project_name: 项目名称
            assigner_name: 分配人姓名
            deadline: 截止日期
            priority: 优先级
            description: 任务描述

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending task assignment notification to {user_id}: {task_name}")

        # 构建卡片内容
        content_lines = [
            f"您已被分配一个新任务",
            "",
            f"**任务名称**: {task_name}",
            f"**所属项目**: {project_name}",
            f"**分配人**: {assigner_name}",
        ]

        if deadline:
            content_lines.append(f"**截止日期**: {deadline}")

        if priority:
            priority_color = self._get_priority_color(priority)
            content_lines.append(f"**优先级**: {priority}")

        if description:
            content_lines.append("")
            content_lines.append(f"**任务描述**: {description[:200]}")

        content_lines.append("")
        content_lines.append("请及时查看任务详情并确认接收。")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title="📋 任务分配通知",
            color="blue",
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看任务详情",
                value={"action": "view_task", "task_id": task_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="确认接收",
                value={"action": "accept_task", "task_id": task_id},
                style="primary",
            ),
        ])

        card = card_builder.build()

        # 发送消息
        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    # ==================== 状态变更通知 ====================

    async def send_status_change_notification(
        self,
        user_id: str,
        entity_type: str,  # task/milestone/project
        entity_name: str,
        entity_id: str,
        old_status: str,
        new_status: str,
        changed_by: str,
        change_reason: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送状态变更通知.

        Args:
            user_id: 接收者飞书用户ID
            entity_type: 实体类型
            entity_name: 实体名称
            entity_id: 实体ID
            old_status: 原状态
            new_status: 新状态
            changed_by: 变更人
            change_reason: 变更原因
            project_name: 项目名称

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending status change notification to {user_id}")

        # 状态图标映射
        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "blocked": "🚫",
            "cancelled": "❌",
        }

        old_icon = status_icons.get(old_status, "")
        new_icon = status_icons.get(new_status, "")

        # 构建卡片内容
        content_lines = [
            f"**{entity_type}** 状态已更新",
            "",
            f"**名称**: {entity_name}",
        ]

        if project_name:
            content_lines.append(f"**项目**: {project_name}")

        content_lines.extend([
            "",
            f"**原状态**: {old_icon} {old_status}",
            f"**新状态**: {new_icon} {new_status}",
            f"**变更人**: {changed_by}",
        ])

        if change_reason:
            content_lines.append(f"**变更原因**: {change_reason}")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title="🔄 状态变更通知",
            color=self._get_status_color(new_status),
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看详情",
                value={"action": f"view_{entity_type}", "entity_id": entity_id},
                style="primary",
            ),
        ])

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    # ==================== 延期预警通知 ====================

    async def send_delay_warning_notification(
        self,
        user_id: str,
        entity_type: str,  # task/milestone
        entity_name: str,
        entity_id: str,
        planned_date: str,
        current_progress: Optional[int] = None,
        estimated_delay_days: Optional[int] = None,
        risk_level: str = "medium",
        project_name: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        发送延期预警通知.

        Args:
            user_id: 接收者飞书用户ID
            entity_type: 实体类型
            entity_name: 实体名称
            entity_id: 实体ID
            planned_date: 计划完成日期
            current_progress: 当前进度（百分比）
            estimated_delay_days: 预估延期天数
            risk_level: 风险等级（low/medium/high/critical）
            project_name: 项目名称
            suggestions: 建议措施

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending delay warning notification to {user_id}: {entity_name}")

        # 风险等级颜色
        risk_colors = {
            "low": "turquoise",
            "medium": "orange",
            "high": "red",
            "critical": "red",
        }

        # 构建卡片内容
        content_lines = [
            f"⚠️ **延期预警** - {entity_name}",
            "",
        ]

        if project_name:
            content_lines.append(f"**项目**: {project_name}")

        content_lines.extend([
            f"**计划完成日期**: {planned_date}",
        ])

        if current_progress is not None:
            content_lines.append(f"**当前进度**: {current_progress}%")

        if estimated_delay_days is not None:
            content_lines.append(f"**预估延期**: {estimated_delay_days} 天")

        content_lines.extend([
            f"**风险等级**: {risk_level.upper()}",
        ])

        if suggestions:
            content_lines.append("")
            content_lines.append("**建议措施**:")
            for suggestion in suggestions:
                content_lines.append(f"- {suggestion}")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title=f"⚠️ 延期预警 - {risk_level.upper()}",
            color=risk_colors.get(risk_level, "orange"),
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看详情",
                value={"action": f"view_{entity_type}", "entity_id": entity_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="申请延期",
                value={"action": "request_delay", "entity_id": entity_id, "entity_type": entity_type},
                style="default",
            ),
            LarkCardBuilder.create_button(
                text="调整计划",
                value={"action": "adjust_plan", "entity_id": entity_id, "entity_type": entity_type},
                style="default",
            ),
        ])

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    # ==================== 成本超支预警通知 ====================

    async def send_cost_overrun_notification(
        self,
        user_id: str,
        project_name: str,
        project_id: str,
        budget_amount: float,
        actual_amount: float,
        overrun_percentage: float,
        overrun_amount: float,
        cost_category: Optional[str] = None,
        risk_level: str = "medium",
        suggestions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        发送成本超支预警通知.

        Args:
            user_id: 接收者飞书用户ID
            project_name: 项目名称
            project_id: 项目ID
            budget_amount: 预算金额
            actual_amount: 实际金额
            overrun_percentage: 超支百分比
            overrun_amount: 超支金额
            cost_category: 成本类别
            risk_level: 风险等级
            suggestions: 建议措施

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending cost overrun notification to {user_id}: {project_name}")

        # 风险等级颜色
        risk_colors = {
            "low": "turquoise",
            "medium": "orange",
            "high": "red",
            "critical": "red",
        }

        # 构建卡片内容
        content_lines = [
            f"💰 **成本超支预警**",
            "",
            f"**项目**: {project_name}",
        ]

        if cost_category:
            content_lines.append(f"**成本类别**: {cost_category}")

        content_lines.extend([
            "",
            f"**预算金额**: ¥{budget_amount:,.2f}",
            f"**实际金额**: ¥{actual_amount:,.2f}",
            f"**超支金额**: ¥{overrun_amount:,.2f}",
            f"**超支比例**: {overrun_percentage:.1f}%",
            "",
            f"**风险等级**: {risk_level.upper()}",
        ])

        if suggestions:
            content_lines.append("")
            content_lines.append("**建议措施**:")
            for suggestion in suggestions:
                content_lines.append(f"- {suggestion}")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title=f"💰 成本超支预警 - {risk_level.upper()}",
            color=risk_colors.get(risk_level, "orange"),
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看成本详情",
                value={"action": "view_cost", "project_id": project_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="申请追加预算",
                value={"action": "request_budget_increase", "project_id": project_id},
                style="default",
            ),
            LarkCardBuilder.create_button(
                text="成本分析",
                value={"action": "cost_analysis", "project_id": project_id},
                style="default",
            ),
        ])

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    # ==================== 风险预警通知 ====================

    async def send_risk_warning_notification(
        self,
        user_id: str,
        risk_name: str,
        risk_id: str,
        risk_level: str,  # low/medium/high/critical
        risk_type: Optional[str] = None,
        probability: Optional[int] = None,
        impact: Optional[str] = None,
        project_name: Optional[str] = None,
        description: Optional[str] = None,
        mitigation_plan: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送风险预警通知.

        Args:
            user_id: 接收者飞书用户ID
            risk_name: 风险名称
            risk_id: 风险ID
            risk_level: 风险等级
            risk_type: 风险类型
            probability: 发生概率（百分比）
            impact: 影响描述
            project_name: 项目名称
            description: 风险描述
            mitigation_plan: 缓解计划
            owner: 风险负责人

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending risk warning notification to {user_id}: {risk_name}")

        # 风险等级颜色和图标
        risk_styles = {
            "low": ("turquoise", "🟢"),
            "medium": ("orange", "🟠"),
            "high": ("red", "🔴"),
            "critical": ("red", "🔴"),
        }

        risk_color, risk_icon = risk_styles.get(risk_level, ("grey", "⚪"))

        # 构建卡片内容
        content_lines = [
            f"{risk_icon} **风险预警** - {risk_name}",
            "",
        ]

        if project_name:
            content_lines.append(f"**项目**: {project_name}")

        if risk_type:
            content_lines.append(f"**风险类型**: {risk_type}")

        content_lines.extend([
            f"**风险等级**: {risk_level.upper()}",
        ])

        if probability:
            content_lines.append(f"**发生概率**: {probability}%")

        if impact:
            content_lines.append(f"**影响程度**: {impact}")

        if description:
            content_lines.append("")
            content_lines.append(f"**风险描述**: {description[:200]}")

        if mitigation_plan:
            content_lines.append("")
            content_lines.append(f"**缓解计划**: {mitigation_plan[:200]}")

        if owner:
            content_lines.append(f"**负责人**: {owner}")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title=f"{risk_icon} 风险预警 - {risk_level.upper()}",
            color=risk_color,
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看风险详情",
                value={"action": "view_risk", "risk_id": risk_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="更新缓解计划",
                value={"action": "update_mitigation", "risk_id": risk_id},
                style="default",
            ),
            LarkCardBuilder.create_button(
                text="关闭风险",
                value={"action": "close_risk", "risk_id": risk_id},
                style="danger" if risk_level in ["low", "medium"] else "default",
            ),
        ])

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=user_id,
            card=card,
        )

    # ==================== 审批流程通知 ====================

    async def send_approval_request_notification(
        self,
        approver_id: str,
        approval_type: str,  # weekly_report/cost_change/schedule_change
        approval_id: str,
        title: str,
        applicant_name: str,
        applicant_id: str,
        project_name: Optional[str] = None,
        content_summary: Optional[str] = None,
        urgent: bool = False,
    ) -> Dict[str, Any]:
        """
        发送审批请求通知.

        Args:
            approver_id: 审批人飞书用户ID
            approval_type: 审批类型
            approval_id: 审批ID
            title: 审批标题
            applicant_name: 申请人姓名
            applicant_id: 申请人ID
            project_name: 项目名称
            content_summary: 内容摘要
            urgent: 是否紧急

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending approval request notification to {approver_id}: {title}")

        # 审批类型图标
        type_icons = {
            "weekly_report": "📝",
            "cost_change": "💰",
            "schedule_change": "📅",
        }
        type_icon = type_icons.get(approval_type, "📋")

        # 构建卡片内容
        content_lines = [
            f"您有一个新的审批请求",
            "",
            f"**审批标题**: {title}",
        ]

        if project_name:
            content_lines.append(f"**项目**: {project_name}")

        content_lines.extend([
            f"**申请人**: {applicant_name}",
            f"**审批类型**: {approval_type}",
        ])

        if content_summary:
            content_lines.append("")
            content_lines.append(f"**内容摘要**:")
            content_lines.append(content_summary[:300])

        if urgent:
            content_lines.append("")
            content_lines.append("⚠️ **紧急审批，请尽快处理**")

        # 构建卡片
        header_title = f"{type_icon} 审批请求{' [紧急]' if urgent else ''}"
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title=header_title,
            color="red" if urgent else "blue",
        )
        card_builder.add_markdown("\n".join(content_lines))
        card_builder.add_divider()
        card_builder.add_action([
            LarkCardBuilder.create_button(
                text="查看详情",
                value={"action": "view_approval", "approval_id": approval_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="同意",
                value={"action": "approve", "approval_id": approval_id},
                style="primary",
            ),
            LarkCardBuilder.create_button(
                text="拒绝",
                value={"action": "reject", "approval_id": approval_id},
                style="danger",
            ),
        ])

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=approver_id,
            card=card,
        )

    async def send_approval_result_notification(
        self,
        applicant_id: str,
        approval_type: str,
        approval_id: str,
        title: str,
        result: str,  # approved/rejected
        approver_name: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        发送审批结果通知.

        Args:
            applicant_id: 申请人飞书用户ID
            approval_type: 审批类型
            approval_id: 审批ID
            title: 审批标题
            result: 审批结果
            approver_name: 审批人姓名
            comment: 审批意见

        Returns:
            Dict: 发送结果
        """
        logger.info(f"Sending approval result notification to {applicant_id}: {result}")

        # 结果图标和颜色
        result_styles = {
            "approved": ("✅", "green"),
            "rejected": ("❌", "red"),
        }
        result_icon, result_color = result_styles.get(result, ("📋", "grey"))

        # 构建卡片内容
        content_lines = [
            f"您的审批请求已处理",
            "",
            f"**审批标题**: {title}",
            f"**审批类型**: {approval_type}",
            f"**审批结果**: {result_icon} {result}",
            f"**审批人**: {approver_name}",
        ]

        if comment:
            content_lines.append("")
            content_lines.append(f"**审批意见**: {comment}")

        # 构建卡片
        card_builder = LarkCardBuilder()
        card_builder.set_header(
            title=f"{result_icon} 审批结果通知",
            color=result_color,
        )
        card_builder.add_markdown("\n".join(content_lines))

        card = card_builder.build()

        return await self._client.send_interactive_card(
            receive_id=applicant_id,
            card=card,
        )

    # ==================== 辅助方法 ====================

    def _get_priority_color(self, priority: str) -> str:
        """获取优先级对应颜色."""
        colors = {
            "critical": "red",
            "high": "orange",
            "medium": "blue",
            "low": "turquoise",
        }
        return colors.get(priority.lower(), "blue")

    def _get_status_color(self, status: str) -> str:
        """获取状态对应颜色."""
        colors = {
            "completed": "green",
            "in_progress": "blue",
            "blocked": "red",
            "cancelled": "grey",
            "pending": "turquoise",
        }
        return colors.get(status.lower(), "blue")


# ==================== 全局实例 ====================

_message_sender: Optional[LarkMessageSender] = None


def get_message_sender() -> LarkMessageSender:
    """获取消息发送器实例."""
    global _message_sender
    if _message_sender is None:
        _message_sender = LarkMessageSender()
    return _message_sender