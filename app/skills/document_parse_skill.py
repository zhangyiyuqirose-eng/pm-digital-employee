"""
PM Digital Employee - Document Parse Skill
项目经理数字员工系统 - 文档解析技能

v1.3.0新增：处理用户发送的文档，自动解析并入库
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.skills.base import BaseSkill
from app.orchestrator.schemas import SkillExecutionResult
from app.orchestrator.skill_manifest import SkillManifestBuilder
from app.services.document_parse_service import (
    DocumentParseService,
    DocumentParseResult,
    get_document_parse_service,
)

logger = get_logger(__name__)


class DocumentParseSkill(BaseSkill):
    """
    文档解析技能.

    处理用户发送的文档文件，执行：
    1. 文件下载
    2. 内容解析
    3. 文档分类
    4. 信息提取
    5. 数据入库

    支持的文档类型：
    - DOCX/PDF/TXT/MD（文本文档）
    - XLSX/XLS/CSV（表格文档）
    - PPTX/PPT（演示文档）
    - JPG/PNG/BMP（图片文档，需OCR）
    """

    skill_name = "document_parse"
    display_name = "文档智能解析"
    description = "解析用户发送的项目文档，自动提取信息并入库到项目管理系统"
    version = "1.0.0"

    def __init__(
        self,
        manifest: Optional[Any] = None,
        context: Optional[Any] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """初始化文档解析技能."""
        super().__init__(manifest, context, session)

    async def execute(self) -> SkillExecutionResult:
        """
        执行文档解析.

        从context获取文件信息并调用DocumentParseService处理。

        Returns:
            SkillExecutionResult: 执行结果
        """
        logger.info(f"Executing DocumentParseSkill: user={self.user_id}")

        # 获取文件参数
        file_key = self.get_param("file_key")
        file_name = self.get_param("file_name")
        file_type = self.get_param("file_type", "file")
        file_size = self.get_param("file_size", 0)
        message_id = self.get_param("message_id")

        # 验证必要参数
        if not file_key:
            return self.build_error_result("缺少文件Key参数")

        if not file_name:
            return self.build_error_result("缺少文件名参数")

        # 验证session
        if not self._session:
            return self.build_error_result("数据库会话未初始化")

        # 构建用户上下文
        user_context = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "chat_type": self.get_param("chat_type", "p2p"),
            "project_id": str(self.project_id) if self.project_id else None,
            "project_name": self.get_param("project_name"),
        }

        # 调用文档解析服务
        parse_service = get_document_parse_service(self._session)

        try:
            result = await parse_service.process_document(
                file_key=file_key,
                file_name=file_name,
                file_type=file_type,
                sender_id=self.user_id or "",
                chat_id=self.chat_id or "",
                chat_type=user_context["chat_type"],
                message_id=message_id or "",
                file_size=file_size,
                user_context=user_context,
            )

            # 构建输出
            output = self._build_output(result)

            # 构建展示数据（飞书卡片）
            presentation_data = self._build_card_data(result)

            if result.success:
                return self.build_success_result(
                    output=output,
                    presentation_type="interactive_card",
                    presentation_data=presentation_data,
                )
            else:
                error_msg = str(result.error) if result.error else "文档解析失败"
                return self.build_error_result(error_msg)

        except Exception as e:
            logger.error(f"DocumentParseSkill execution failed: {e}")
            return self.build_error_result(f"文档解析失败: {str(e)}")

    def _build_output(self, result: DocumentParseResult) -> Dict[str, Any]:
        """构建输出数据."""
        return {
            "parse_record_id": result.parse_record_id,
            "success": result.success,
            "confidence": result.confidence,
            "imported_count": result.imported_count,
            "requires_confirmation": result.requires_confirmation,
        }

    def _build_card_data(self, result: DocumentParseResult) -> Dict[str, Any]:
        """构建飞书卡片数据."""
        if not result.success:
            return self._build_error_card(result)

        if result.requires_confirmation:
            return self._build_pending_card(result)

        return self._build_success_card(result)

    def _build_success_card(self, result: DocumentParseResult) -> Dict[str, Any]:
        """构建成功卡片."""
        confidence_percent = int(result.confidence * 100)

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "✅ 文档解析成功"},
                "template": "green",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**置信度**: {confidence_percent}%\n**入库数据**: {result.imported_count} 条",
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看详情"},
                            "type": "primary",
                            "value": {
                                "action": "view_parse_detail",
                                "parse_id": result.parse_record_id,
                            },
                        },
                    ],
                },
            ],
        }

    def _build_pending_card(self, result: DocumentParseResult) -> Dict[str, Any]:
        """构建待确认卡片."""
        confidence_percent = int(result.confidence * 100)

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "⚠️ 数据解析待确认"},
                "template": "orange",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**置信度**: {confidence_percent}%\n\n请确认数据是否正确后入库。",
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "确认入库"},
                            "type": "primary",
                            "value": {
                                "action": "confirm_parse",
                                "parse_id": result.parse_record_id,
                            },
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "取消"},
                            "type": "default",
                            "value": {
                                "action": "cancel_parse",
                                "parse_id": result.parse_record_id,
                            },
                        },
                    ],
                },
            ],
        }

    def _build_error_card(self, result: DocumentParseResult) -> Dict[str, Any]:
        """构建错误卡片."""
        error_msg = str(result.error) if result.error else "未知错误"

        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "❌ 文档解析失败"},
                "template": "red",
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**错误信息**: {error_msg}\n\n请检查文档格式是否正确，或联系管理员。",
                },
            ],
        }

    @classmethod
    def get_manifest(cls) -> Any:
        """获取Skill Manifest."""
        builder = SkillManifestBuilder()
        builder.set_name(cls.skill_name, cls.display_name)
        builder.set_description(cls.description)
        builder.set_version(cls.version)

        # 定义参数
        builder.add_param(
            name="file_key",
            type="string",
            required=True,
            description="飞书文件Key",
        )
        builder.add_param(
            name="file_name",
            type="string",
            required=True,
            description="文件名",
        )
        builder.add_param(
            name="file_type",
            type="string",
            required=False,
            default="file",
            description="文件类型（file/image）",
        )
        builder.add_param(
            name="file_size",
            type="integer",
            required=False,
            default=0,
            description="文件大小（字节）",
        )
        builder.add_param(
            name="message_id",
            type="string",
            required=False,
            description="飞书消息ID",
        )
        builder.add_param(
            name="chat_type",
            type="string",
            required=False,
            default="p2p",
            description="会话类型",
        )

        # 定义输出
        builder.add_output(
            name="parse_record_id",
            type="string",
            description="解析记录ID",
        )
        builder.add_output(
            name="confidence",
            type="float",
            description="提取置信度",
        )
        builder.add_output(
            name="imported_count",
            type="integer",
            description="入库数据条数",
        )

        # 设置触发方式
        builder.set_trigger_type("file_message")  # 文件消息触发
        builder.set_category("data_entry")        # 数据录入类

        return builder.build()


class DocumentConfirmSkill(BaseSkill):
    """
    文档确认技能.

    处理用户对文档解析结果的确认操作。
    """

    skill_name = "document_confirm"
    display_name = "文档确认"
    description = "确认文档解析结果并执行入库"
    version = "1.0.0"

    async def execute(self) -> SkillExecutionResult:
        """执行文档确认."""
        logger.info(f"Executing DocumentConfirmSkill: user={self.user_id}")

        parse_id = self.get_param("parse_id")
        action = self.get_param("action", "confirm")
        edited_data = self.get_param("edited_data")
        project_id = self.get_param("project_id")

        if not parse_id:
            return self.build_error_result("缺少解析记录ID")

        if not self._session:
            return self.build_error_result("数据库会话未初始化")

        # 构建用户上下文
        user_context = {
            "user_id": self.user_id,
            "user_name": self.get_param("user_name"),
        }

        # 调用确认服务
        parse_service = get_document_parse_service(self._session)

        try:
            # 将parse_id转为UUID
            parse_uuid = uuid.UUID(parse_id)

            result = await parse_service.confirm_parse(
                parse_id=parse_uuid,
                action=action,
                edited_data=edited_data,
                project_id=uuid.UUID(project_id) if project_id else None,
                user_context=user_context,
            )

            output = {
                "success": result.success,
                "imported_count": result.imported_count,
            }

            if result.success:
                return self.build_success_result(
                    output=output,
                    presentation_type="text",
                    presentation_data={
                        "text": f"✅ 数据已入库，共 {result.imported_count} 条",
                    },
                )
            else:
                error_msg = str(result.error) if result.error else "确认失败"
                return self.build_error_result(error_msg)

        except Exception as e:
            logger.error(f"DocumentConfirmSkill execution failed: {e}")
            return self.build_error_result(f"确认失败: {str(e)}")

    @classmethod
    def get_manifest(cls) -> Any:
        """获取Skill Manifest."""
        builder = SkillManifestBuilder()
        builder.set_name(cls.skill_name, cls.display_name)
        builder.set_description(cls.description)
        builder.set_version(cls.version)

        builder.add_param(
            name="parse_id",
            type="string",
            required=True,
            description="解析记录ID",
        )
        builder.add_param(
            name="action",
            type="string",
            required=True,
            description="确认动作（confirm/edit/cancel）",
        )
        builder.add_param(
            name="edited_data",
            type="object",
            required=False,
            description="编辑后的数据",
        )
        builder.add_param(
            name="project_id",
            type="string",
            required=False,
            description="项目ID",
        )

        builder.set_trigger_type("card_action")  # 卡片按钮触发
        builder.set_category("data_entry")

        return builder.build()