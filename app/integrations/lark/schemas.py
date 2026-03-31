"""
PM Digital Employee - Lark Schemas
项目经理数字员工系统 - 飞书事件、消息、卡片的Pydantic模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 事件模型 ====================


class LarkEventHeader(BaseModel):
    """飞书事件头."""

    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    create_time: str = Field(..., description="事件创建时间")
    token: Optional[str] = Field(None, description="验证Token")
    app_id: Optional[str] = Field(None, description="应用ID")
    tenant_key: Optional[str] = Field(None, description="租户Key")


class LarkEvent(BaseModel):
    """飞书事件模型."""

    schema_version: Optional[str] = Field(None, alias="schema", description="Schema版本")
    header: LarkEventHeader = Field(..., description="事件头")
    event: Dict[str, Any] = Field(..., description="事件体")


class LarkWebhookRequest(BaseModel):
    """飞书Webhook请求模型."""

    schema: Optional[str] = Field(None, description="Schema版本")
    header: Optional[Dict[str, Any]] = Field(None, description="事件头")
    event: Optional[Dict[str, Any]] = Field(None, description="事件体")

    # URL验证专用字段
    challenge: Optional[str] = Field(None, description="挑战码（URL验证）")
    token: Optional[str] = Field(None, description="Token（URL验证）")
    type: Optional[str] = Field(None, description="类型（URL验证）")


# ==================== 消息模型 ====================


class LarkMessageSender(BaseModel):
    """飞书消息发送者."""

    sender_id: Optional[Dict[str, str]] = Field(None, description="发送者ID")
    sender_type: Optional[str] = Field(None, description="发送者类型")
    tenant_key: Optional[str] = Field(None, description="租户Key")


class LarkMessage(BaseModel):
    """飞书消息模型."""

    message_id: str = Field(..., description="消息ID")
    root_id: Optional[str] = Field(None, description="根消息ID")
    parent_id: Optional[str] = Field(None, description="父消息ID")
    create_time: Optional[str] = Field(None, description="创建时间")
    chat_id: str = Field(..., description="会话ID")
    chat_type: Optional[str] = Field(None, description="会话类型")
    message_type: str = Field(..., description="消息类型")
    content: Optional[str] = Field(None, description="消息内容")
    mentions: Optional[List[Dict[str, Any]]] = Field(None, description="@列表")

    # 发送者信息
    sender: Optional[LarkMessageSender] = Field(None, description="发送者")


class LarkMessageEvent(BaseModel):
    """飞书消息事件."""

    sender: Dict[str, Any] = Field(..., description="发送者信息")
    message: LarkMessage = Field(..., description="消息内容")


# ==================== 卡片模型 ====================


class LarkCardAction(BaseModel):
    """飞书卡片动作."""

    value: Dict[str, Any] = Field(default_factory=dict, description="动作值")
    option: Optional[str] = Field(None, description="选项")
    tag: Optional[str] = Field(None, description="标签")


class LarkCardContext(BaseModel):
    """飞书卡片上下文."""

    open_message_id: Optional[str] = Field(None, description="消息ID")
    open_chat_id: Optional[str] = Field(None, description="会话ID")
    open_app_id: Optional[str] = Field(None, description="应用ID")
    tenant_key: Optional[str] = Field(None, description="租户Key")


class LarkCardCallback(BaseModel):
    """飞书卡片回调请求."""

    challenge: Optional[str] = Field(None, description="挑战码")
    type: Optional[str] = Field(None, description="类型")
    token: Optional[str] = Field(None, description="Token")
    action: Optional[LarkCardAction] = Field(None, description="动作")
    open_id: Optional[str] = Field(None, description="用户OpenID")
    user_id: Optional[str] = Field(None, description="用户ID")
    union_id: Optional[str] = Field(None, description="用户UnionID")
    open_message_id: Optional[str] = Field(None, description="消息ID")
    open_chat_id: Optional[str] = Field(None, description="会话ID")
    tenant_key: Optional[str] = Field(None, description="租户Key")
    context: Optional[LarkCardContext] = Field(None, description="上下文")


# ==================== 用户模型 ====================


class LarkUser(BaseModel):
    """飞书用户模型."""

    open_id: Optional[str] = Field(None, description="OpenID")
    user_id: Optional[str] = Field(None, description="用户ID")
    union_id: Optional[str] = Field(None, description="UnionID")
    name: Optional[str] = Field(None, description="姓名")
    en_name: Optional[str] = Field(None, description="英文名")
    nickname: Optional[str] = Field(None, description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    mobile: Optional[str] = Field(None, description="手机号")
    gender: Optional[int] = Field(None, description="性别")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    status: Optional[Dict[str, Any]] = Field(None, description="状态")
    department_ids: Optional[List[str]] = Field(None, description="部门ID列表")
    leader_user_id: Optional[str] = Field(None, description="上级ID")
    city: Optional[str] = Field(None, description="城市")
    country: Optional[str] = Field(None, description="国家")
    work_station: Optional[str] = Field(None, description="工位")
    join_time: Optional[int] = Field(None, description="入职时间")
    employee_no: Optional[str] = Field(None, description="工号")
    positions: Optional[List[Dict[str, Any]]] = Field(None, description="职位列表")


# ==================== 群模型 ====================


class LarkChat(BaseModel):
    """飞书群聊模型."""

    chat_id: str = Field(..., description="群ID")
    name: Optional[str] = Field(None, description="群名称")
    description: Optional[str] = Field(None, description="群描述")
    owner_id: Optional[str] = Field(None, description="群主ID")
    owner_id_type: Optional[str] = Field(None, description="群主ID类型")
    member_count: Optional[int] = Field(None, description="成员数量")
    user_id_list: Optional[List[str]] = Field(None, description="用户ID列表")
    group_message_pin: Optional[str] = Field(None, description="群置顶消息")
    join_message_visibility: Optional[str] = Field(None, description="入群消息可见性")
    leave_message_visibility: Optional[str] = Field(None, description="离群消息可见性")
    members: Optional[List[Dict[str, Any]]] = Field(None, description="成员列表")


# ==================== 响应模型 ====================


class LarkSendMessageResponse(BaseModel):
    """发送消息响应."""

    code: int = Field(..., description="状态码")
    msg: str = Field(..., description="消息")
    data: Optional[Dict[str, Any]] = Field(None, description="数据")


# ==================== 交互式卡片构建器 ====================


class LarkCardBuilder:
    """飞书交互式卡片构建器."""

    def __init__(self) -> None:
        """初始化卡片构建器."""
        self._elements: List[Dict[str, Any]] = []
        self._header: Optional[Dict[str, Any]] = None

    def set_header(self, title: str, template: str = "blue") -> "LarkCardBuilder":
        """
        设置卡片头部.

        Args:
            title: 标题
            template: 模板颜色

        Returns:
            LarkCardBuilder: 构建器实例
        """
        self._header = {
            "title": {"tag": "plain_text", "content": title},
            "template": template,
        }
        return self

    def add_markdown(self, content: str) -> "LarkCardBuilder":
        """
        添加Markdown内容.

        Args:
            content: Markdown内容

        Returns:
            LarkCardBuilder: 构建器实例
        """
        self._elements.append(
            {
                "tag": "markdown",
                "content": content,
            }
        )
        return self

    def add_divider(self) -> "LarkCardBuilder":
        """添加分割线."""
        self._elements.append({"tag": "hr"})
        return self

    def add_field(self, fields: List[Dict[str, str]]) -> "LarkCardBuilder":
        """
        添加字段列表.

        Args:
            fields: 字段列表

        Returns:
            LarkCardBuilder: 构建器实例
        """
        self._elements.append(
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f.get("content", "")}}
                    for f in fields
                ],
            }
        )
        return self

    def add_action(
        self,
        actions: List[Dict[str, Any]],
    ) -> "LarkCardBuilder":
        """
        添加动作按钮.

        Args:
            actions: 动作列表

        Returns:
            LarkCardBuilder: 构建器实例
        """
        self._elements.append(
            {
                "tag": "action",
                "actions": actions,
            }
        )
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建卡片.

        Returns:
            Dict[str, Any]: 卡片JSON
        """
        card: Dict[str, Any] = {
            "type": "template",
            "data": {
                "template": {
                    "type": "card",
                    "elements": self._elements,
                },
            },
        }

        if self._header:
            card["data"]["template"]["header"] = self._header

        return card

    @staticmethod
    def create_button(
        text: str,
        value: Dict[str, Any],
        style: str = "primary",
    ) -> Dict[str, Any]:
        """
        创建按钮元素.

        Args:
            text: 按钮文本
            value: 按钮值
            style: 样式

        Returns:
            Dict[str, Any]: 按钮元素
        """
        return {
            "tag": "button",
            "text": {"tag": "plain_text", "content": text},
            "value": value,
            "style": style,
        }