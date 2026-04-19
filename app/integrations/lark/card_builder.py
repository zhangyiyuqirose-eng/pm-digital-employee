"""
PM Digital Employee - Card Builder
飞书交互卡片流式构建器

参考提示词Part 2.1标准实现。
支持流式API设计，链式调用构建复杂卡片。
"""

from typing import Any, Dict, List, Optional, Self
import json


class CardBuilder:
    """
    流式卡片构建器.

    支持链式调用，优雅构建飞书交互卡片。

    Example:
        card = (
            CardBuilder()
            .header("项目总览", template="blue")
            .div_module("整体进度: 82%")
            .hr()
            .markdown_module("**风险预警**\\n- 高风险")
            .action_module([
                {"tag": "button", "text": "查看详情", "url": "..."}
            ])
            .build()
        )
    """

    def __init__(self) -> None:
        """初始化构建器."""
        self._config: Dict[str, Any] = {
            "config": {
                "wide_screen_mode": True,
            },
            "elements": [],
        }
        self._header: Optional[Dict[str, Any]] = None

    def header(
        self,
        title: str,
        template: str = "blue",
        subtitle: Optional[str] = None,
    ) -> Self:
        """
        添加标题区.

        Args:
            title: 标题文本
            template: 模板颜色（blue/green/red/orange/grey）
            subtitle: 副标题

        Returns:
            Self: 构建器实例
        """
        self._header = {
            "title": {
                "tag": "plain_text",
                "content": title,
            },
            "template": template,
        }
        if subtitle:
            self._header["subtitle"] = {
                "tag": "plain_text",
                "content": subtitle,
            }
        return self

    def div_module(
        self,
        text: str,
        field_id: Optional[str] = None,
    ) -> Self:
        """
        添加文本模块.

        Args:
            text: 文本内容
            field_id: 字段ID（可选）

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "div",
            "text": {
                "tag": "plain_text",
                "content": text,
            },
        }
        if field_id:
            element["field_id"] = field_id
        self._config["elements"].append(element)
        return self

    def markdown_module(
        self,
        content: str,
        field_id: Optional[str] = None,
    ) -> Self:
        """
        添加Markdown模块.

        Args:
            content: Markdown内容
            field_id: 字段ID（可选）

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content,
            },
        }
        if field_id:
            element["field_id"] = field_id
        self._config["elements"].append(element)
        return self

    def hr(self) -> Self:
        """
        添加分割线.

        Returns:
            Self: 构建器实例
        """
        self._config["elements"].append({"tag": "hr"})
        return self

    def note_module(
        self,
        text: str,
    ) -> Self:
        """
        添加备注模块.

        Args:
            text: 备注文本

        Returns:
            Self: 构建器实例
        """
        self._config["elements"].append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": text,
                }
            ],
        })
        return self

    def img_module(
        self,
        img_key: str,
        alt: Optional[str] = None,
        preview: bool = True,
    ) -> Self:
        """
        添加图片模块.

        Args:
            img_key: 图片key
            alt: 替代文本
            preview: 是否预览

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "img",
            "img_key": img_key,
            "preview": preview,
        }
        if alt:
            element["alt"] = {
                "tag": "plain_text",
                "content": alt,
            }
        self._config["elements"].append(element)
        return self

    def action_module(
        self,
        actions: List[Dict[str, Any]],
    ) -> Self:
        """
        添加按钮组.

        Args:
            actions: 按钮列表

        Returns:
            Self: 构建器实例
        """
        self._config["elements"].append({
            "tag": "action",
            "actions": actions,
        })
        return self

    def column_set_module(
        self,
        columns: List[Dict[str, Any]],
        flex_mode: str = "none",
        background_style: str = "default",
    ) -> Self:
        """
        添加多列布局.

        Args:
            columns: 列列表
            flex_mode: 弹性模式
            background_style: 背景样式

        Returns:
            Self: 构建器实例
        """
        self._config["elements"].append({
            "tag": "column_set",
            "flex_mode": flex_mode,
            "background_style": background_style,
            "columns": columns,
        })
        return self

    def select_static_module(
        self,
        placeholder: str,
        options: List[Dict[str, str]],
        value: Optional[str] = None,
        field_id: Optional[str] = None,
    ) -> Self:
        """
        添加静态下拉选择.

        Args:
            placeholder: 占位文本
            options: 选项列表
            value: 默认值
            field_id: 字段ID

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "select_static",
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder,
            },
            "options": [
                {
                    "text": {"tag": "plain_text", "content": opt.get("text", "")},
                    "value": opt.get("value", ""),
                }
                for opt in options
            ],
        }
        if value:
            element["value"] = value
        if field_id:
            element["field_id"] = field_id
        self._config["elements"].append(element)
        return self

    def input_module(
        self,
        placeholder: str,
        default_value: Optional[str] = None,
        field_id: Optional[str] = None,
        required: bool = False,
    ) -> Self:
        """
        添加输入框.

        Args:
            placeholder: 占位文本
            default_value: 默认值
            field_id: 字段ID
            required: 是否必填

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "input",
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder,
            },
            "required": required,
        }
        if default_value:
            element["default_value"] = default_value
        if field_id:
            element["field_id"] = field_id
        self._config["elements"].append(element)
        return self

    def date_picker_module(
        self,
        placeholder: str,
        initial_date: Optional[str] = None,
        field_id: Optional[str] = None,
    ) -> Self:
        """
        添加日期选择器.

        Args:
            placeholder: 占位文本
            initial_date: 初始日期
            field_id: 字段ID

        Returns:
            Self: 构建器实例
        """
        element = {
            "tag": "date_picker",
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder,
            },
        }
        if initial_date:
            element["initial_date"] = initial_date
        if field_id:
            element["field_id"] = field_id
        self._config["elements"].append(element)
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建卡片JSON.

        Returns:
            Dict: 卡片配置
        """
        card = self._config.copy()
        if self._header:
            card["header"] = self._header
        return card

    # ============================================
    # 预置模板方法
    # ============================================

    @classmethod
    def build_project_overview_card(
        cls,
        project_name: str,
        status: str,
        progress: int,
        risks_count: int,
    ) -> Dict[str, Any]:
        """
        构建项目总览卡片模板.

        Args:
            project_name: 项目名称
            status: 项目状态
            progress: 进度百分比
            risks_count: 风险数量

        Returns:
            Dict: 卡片配置
        """
        return (
            cls()
            .header(project_name, template="blue", subtitle=f"状态: {status}")
            .markdown_module(f"**整体进度**: {progress}%")
            .hr()
            .markdown_module(f"**风险预警**: 共 {risks_count} 项风险")
            .action_module([
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "查看详情"},
                    "type": "primary",
                }
            ])
            .build()
        )

    @classmethod
    def build_confirmation_card(
        cls,
        title: str,
        message: str,
        confirm_action: Dict[str, Any],
        cancel_action: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建确认卡片模板.

        Args:
            title: 标题
            message: 消息内容
            confirm_action: 确认按钮配置
            cancel_action: 取消按钮配置

        Returns:
            Dict: 卡片配置
        """
        actions = [confirm_action]
        if cancel_action:
            actions.append(cancel_action)

        return (
            cls()
            .header(title, template="orange")
            .div_module(message)
            .action_module(actions)
            .build()
        )

    @classmethod
    def build_error_card(
        cls,
        error_title: str,
        error_message: str,
    ) -> Dict[str, Any]:
        """
        构建错误提示卡片模板.

        Args:
            error_title: 错误标题
            error_message: 错误消息

        Returns:
            Dict: 卡片配置
        """
        return (
            cls()
            .header(error_title, template="red")
            .div_module(error_message)
            .build()
        )

    @classmethod
    def build_success_card(
        cls,
        title: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        构建成功提示卡片模板.

        Args:
            title: 标题
            message: 成功消息

        Returns:
            Dict: 卡片配置
        """
        return (
            cls()
            .header(title, template="green")
            .div_module(message)
            .build()
        )


# 按钮构建辅助类
class ButtonBuilder:
    """按钮构建器."""

    @staticmethod
    def primary(
        text: str,
        url: Optional[str] = None,
        callback_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建主要按钮.

        Args:
            text: 按钮文本
            url: 链接URL
            callback_value: 回调值

        Returns:
            Dict: 按钮配置
        """
        button = {
            "tag": "button",
            "text": {"tag": "plain_text", "content": text},
            "type": "primary",
        }
        if url:
            button["url"] = url
        if callback_value:
            button["value"] = callback_value
        return button

    @staticmethod
    def secondary(
        text: str,
        url: Optional[str] = None,
        callback_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """构建次要按钮."""
        button = {
            "tag": "button",
            "text": {"tag": "plain_text", "content": text},
            "type": "default",
        }
        if url:
            button["url"] = url
        if callback_value:
            button["value"] = callback_value
        return button

    @staticmethod
    def danger(
        text: str,
        callback_value: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """构建危险按钮."""
        button = {
            "tag": "button",
            "text": {"tag": "plain_text", "content": text},
            "type": "danger",
        }
        if callback_value:
            button["value"] = callback_value
        return button


__all__ = ["CardBuilder", "ButtonBuilder"]