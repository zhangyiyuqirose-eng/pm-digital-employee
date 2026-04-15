"""
PM Digital Employee - Lark (Feishu) Integration Schemas
项目经理数字员工系统 - 飞书开放平台数据模型与卡片构建器

飞书作为唯一用户交互入口。
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 颜色模板枚举 ====================


class LarkCardColor(str, Enum):
    """飞书卡片颜色模板."""

    BLUE = "blue"
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    PURPLE = "purple"
    INDIGO = "indigo"
    GREY = "grey"
    TURQUOISE = "turquoise"
    YELLOW = "yellow"
    DEFAULT = "default"
    PRIMARY = "primary"
    DANGER = "danger"
    WARNING = "warning"
    SUCCESS = "success"


# ==================== 飞书消息模型 ====================


class LarkMessage(BaseModel):
    """飞书消息数据模型."""

    message_id: str = ""
    chat_id: str = ""
    chat_type: str = "p2p"
    message_type: str = "text"
    content: str = ""
    sender_user_id: str = ""
    sender_open_id: str = ""
    create_time: str = ""
    update_time: str = ""
    parent_id: str = ""
    root_id: str = ""


class LarkEvent(BaseModel):
    """飞书事件数据模型."""

    event_id: str = ""
    event_type: str = ""
    schema_version: str = "2.0"
    token: str = ""
    create_time: str = ""
    app_id: str = ""
    tenant_key: str = ""

    # im.message.receive_v1 事件特有字段
    message: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None


class LarkCallbackRequest(BaseModel):
    """飞书卡片交互回调请求."""

    open_chat_id: str = ""
    open_message_id: str = ""
    open_id: str = ""
    user_id: str = ""
    tenant_key: str = ""
    token: str = ""
    action: Dict[str, Any] = Field(default_factory=dict)
    value: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = ""


# ==================== 飞书用户/群模型 ====================


class LarkUser(BaseModel):
    """飞书用户信息."""

    open_id: str = ""
    user_id: str = ""
    union_id: str = ""
    name: str = ""
    avatar_url: str = ""
    email: str = ""
    mobile: str = ""
    department_ids: List[str] = Field(default_factory=list)


class LarkChat(BaseModel):
    """飞书群聊信息."""

    chat_id: str = ""
    name: str = ""
    description: str = ""
    owner_id: str = ""
    members: List[str] = Field(default_factory=list)


# ==================== 飞书卡片构建器 ====================


class LarkCardBuilder:
    """
    飞书交互式卡片构建器.

    实现飞书开放平台 Interactive Card 的 fluent API 构建方式。
    生成的 JSON 结构符合飞书消息卡片规范:
    {
        "config": {"wide_screen_mode": true},
        "header": {"title": {"tag": "plain_text", "content": "..."}, "template": "blue"},
        "elements": [
            {"tag": "markdown", "content": "..."},
            {"tag": "hr"},
            {"tag": "fields", "fields": [...]},
            {"tag": "action", "actions": [...]}
        ]
    }
    """

    def __init__(self) -> None:
        """初始化卡片构建器."""
        self._config: Dict[str, Any] = {"wide_screen_mode": True}
        self._header: Optional[Dict[str, Any]] = None
        self._elements: List[Dict[str, Any]] = []

    def set_header(self, title: str, color: str = "blue") -> "LarkCardBuilder":
        """
        设置卡片头部标题和颜色.

        Args:
            title: 标题文本
            color: 颜色模板 (blue/green/red/orange/purple/indigo/grey等)
        """
        self._header = {
            "title": {
                "tag": "plain_text",
                "content": title,
            },
            "template": color,
        }
        return self

    def add_markdown(self, content: str) -> "LarkCardBuilder":
        """
        添加Markdown内容元素.

        Args:
            content: Markdown格式文本
        """
        self._elements.append({
            "tag": "markdown",
            "content": content,
        })
        return self

    def add_divider(self) -> "LarkCardBuilder":
        """添加分割线元素."""
        self._elements.append({"tag": "hr"})
        return self

    def add_field(self, fields: List[Dict[str, str]]) -> "LarkCardBuilder":
        """
        添加字段列表元素.

        Args:
            fields: 字段列表，每项包含 "content" 键
        """
        lark_fields = []
        for f in fields:
            lark_fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f.get("content", ""),
                },
            })

        self._elements.append({
            "tag": "field",
            "fields": lark_fields,
        })
        return self

    def add_action(self, actions: List[Dict[str, Any]]) -> "LarkCardBuilder":
        """
        添加操作按钮容器.

        Args:
            actions: 按钮元素列表
        """
        self._elements.append({
            "tag": "action",
            "actions": actions,
        })
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建飞书卡片JSON.

        Returns:
            Dict: 符合飞书卡片规范的JSON对象
        """
        card: Dict[str, Any] = {
            "config": self._config,
        }

        if self._header:
            card["header"] = self._header

        card["elements"] = self._elements

        return card

    @staticmethod
    def create_button(
        text: str,
        value: Dict[str, Any],
        style: str = "primary",
    ) -> Dict[str, Any]:
        """
        创建飞书交互卡片按钮.

        Args:
            text: 按钮文本
            value: 按钮回调值 (JSON对象)
            style: 按钮样式 (primary/danger/default)

        Returns:
            Dict: 飞书按钮元素JSON
        """
        style_map = {
            "primary": "primary",
            "danger": "danger",
            "default": "default",
            "green": "primary",
            "red": "danger",
            "blue": "primary",
        }

        return {
            "tag": "button",
            "text": {
                "tag": "plain_text",
                "content": text,
            },
            "type": style_map.get(style, style),
            "value": value,
        }

    @staticmethod
    def create_text_notice(
        title: str,
        desc: str,
        source_desc: str = "",
    ) -> Dict[str, Any]:
        """
        创建文本通知卡片（静态方法）.

        Args:
            title: 标题
            desc: 描述内容
            source_desc: 来源描述

        Returns:
            Dict: 卡片JSON
        """
        builder = LarkCardBuilder()
        builder.set_header(title, "blue")
        builder.add_markdown(desc)
        if source_desc:
            builder.add_divider()
            builder.add_markdown(f"来源: {source_desc}")
        return builder.build()

    @staticmethod
    def create_button_interaction(
        title: str,
        desc: str,
        buttons: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        创建带按钮交互的卡片（静态方法）.

        Args:
            title: 标题
            desc: 描述内容
            buttons: 按钮列表 [{"text": "...", "key": "..."}]

        Returns:
            Dict: 卡片JSON
        """
        builder = LarkCardBuilder()
        builder.set_header(title, "blue")
        builder.add_markdown(desc)
        builder.add_divider()

        actions = []
        for btn in buttons:
            key = btn.get("key", btn.get("text", ""))
            actions.append(
                LarkCardBuilder.create_button(
                    text=btn["text"],
                    value={"action": key},
                    style="primary" if btn.get("key", "").startswith("confirm") else "default",
                ),
            )

        builder.add_action(actions)
        return builder.build()
