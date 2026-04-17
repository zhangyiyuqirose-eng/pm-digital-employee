"""
PM Digital Employee - Lark Card Forms
项目经理数字员工系统 - 飞书卡片表单模板

提供数据录入的飞书卡片表单JSON模板。
"""

import json
from typing import Any, Dict, List, Optional

from app.integrations.lark.schemas import LarkCardBuilder


# ==================== 项目创建卡片 ====================

def build_project_create_card() -> Dict[str, Any]:
    """
    构建项目创建卡片表单.

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    # 标题
    builder.set_header("创建新项目", "blue")
    
    # 表单说明
    builder.add_markdown("请填写项目基本信息：")
    
    # 表单容器（使用input组件模拟表单）
    form_elements = [
        {
            "tag": "input",
            "name": "project_name",
            "placeholder": "请输入项目名称",
            "required": True,
        },
        {
            "tag": "input",
            "name": "project_code",
            "placeholder": "项目编码（可选，自动生成）",
        },
        {
            "tag": "select_static",
            "name": "project_type",
            "placeholder": "选择项目类型",
            "options": [
                {"text": "研发项目", "value": "研发项目"},
                {"text": "基建项目", "value": "基建项目"},
                {"text": "运维项目", "value": "运维项目"},
            ],
        },
        {
            "tag": "textarea",
            "name": "project_description",
            "placeholder": "项目描述",
        },
        {
            "tag": "date_picker",
            "name": "start_date",
            "placeholder": "计划开始日期",
        },
        {
            "tag": "date_picker",
            "name": "end_date",
            "placeholder": "计划结束日期",
        },
        {
            "tag": "input",
            "name": "total_budget",
            "placeholder": "总预算（元）",
            "input_type": "number",
        },
    ]
    
    # 提交按钮
    builder.add_action(
        builder.create_button(
            text="提交创建",
            value={"action": "create_project"},
            style="primary",
        )
    )
    
    return builder.build()


# ==================== 任务录入卡片 ====================

def build_task_create_card(project_id: str, project_name: str) -> Dict[str, Any]:
    """
    构建任务录入卡片表单.

    Args:
        project_id: 项目ID
        project_name: 项目名称

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    builder.set_header(f"录入任务 - {project_name}", "green")
    builder.add_markdown("请填写任务信息：")
    
    # 提交按钮
    builder.add_action(
        builder.create_button(
            text="提交任务",
            value={"action": "create_task", "project_id": project_id},
            style="primary",
        )
    )
    
    return builder.build()


# ==================== 风险登记卡片 ====================

def build_risk_create_card(project_id: str, project_name: str) -> Dict[str, Any]:
    """
    构建风险登记卡片表单.

    Args:
        project_id: 项目ID
        project_name: 项目名称

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    builder.set_header(f"登记风险 - {project_name}", "red")
    builder.add_markdown("请填写风险信息：")
    
    builder.add_action(
        builder.create_button(
            text="提交风险",
            value={"action": "create_risk", "project_id": project_id},
            style="danger",
        )
    )
    
    return builder.build()


# ==================== 成本录入卡片 ====================

def build_cost_create_card(project_id: str, project_name: str) -> Dict[str, Any]:
    """
    构建成本录入卡片表单.

    Args:
        project_id: 项目ID
        project_name: 项目名称

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    builder.set_header(f"录入成本 - {project_name}", "orange")
    builder.add_markdown("请填写成本信息：")
    
    builder.add_action(
        builder.create_button(
            text="提交成本",
            value={"action": "create_cost", "project_id": project_id},
            style="primary",
        )
    )
    
    return builder.build()


# ==================== 里程碑更新卡片 ====================

def build_milestone_create_card(project_id: str, project_name: str) -> Dict[str, Any]:
    """
    构建里程碑卡片表单.

    Args:
        project_id: 项目ID
        project_name: 项目名称

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    builder.set_header(f"添加里程碑 - {project_name}", "purple")
    builder.add_markdown("请填写里程碑信息：")
    
    builder.add_action(
        builder.create_button(
            text="提交里程碑",
            value={"action": "create_milestone", "project_id": project_id},
            style="primary",
        )
    )
    
    return builder.build()


# ==================== 数据录入入口卡片 ====================

def build_data_entry_menu_card(project_id: str, project_name: str) -> Dict[str, Any]:
    """
    构建数据录入菜单卡片.

    用户选择要录入的数据类型。

    Args:
        project_id: 项目ID
        project_name: 项目名称

    Returns:
        Dict: 卡片JSON
    """
    builder = LarkCardBuilder()
    
    builder.set_header(f"数据录入 - {project_name}", "blue")
    builder.add_markdown("请选择要录入的数据类型：")
    builder.add_divider()
    
    # 功能按钮
    buttons = [
        builder.create_button(
            text="📝 录入任务",
            value={"action": "menu_task", "project_id": project_id},
            style="primary",
        ),
        builder.create_button(
            text="⚠️ 登记风险",
            value={"action": "menu_risk", "project_id": project_id},
            style="danger",
        ),
        builder.create_button(
            text="💰 录入成本",
            value={"action": "menu_cost", "project_id": project_id},
            style="default",
        ),
        builder.create_button(
            text="🎯 添加里程碑",
            value={"action": "menu_milestone", "project_id": project_id},
            style="default",
        ),
    ]
    
    builder.add_action(buttons)
    
    return builder.build()


# ==================== 卡片模板导出 ====================

CARD_TEMPLATES = {
    "project_create": build_project_create_card,
    "task_create": build_task_create_card,
    "risk_create": build_risk_create_card,
    "cost_create": build_cost_create_card,
    "milestone_create": build_milestone_create_card,
    "data_entry_menu": build_data_entry_menu_card,
}


def get_card_template(name: str, **kwargs) -> Dict[str, Any]:
    """
    获取卡片模板.

    Args:
        name: 模板名称
        **kwargs: 模板参数

    Returns:
        Dict: 卡片JSON
    """
    builder_func = CARD_TEMPLATES.get(name)
    if not builder_func:
        raise ValueError(f"Unknown card template: {name}")
    
    return builder_func(**kwargs)