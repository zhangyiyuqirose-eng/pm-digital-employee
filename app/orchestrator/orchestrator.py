"""
PM Digital Employee - Orchestrator
项目经理数字员工系统 - 主编排引擎

协调意图识别、状态流转、Skill执行、结果展示的完整流程。
"""

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorCode, OrchestratorError, SkillNotFoundError
from app.core.logging import get_logger
from app.integrations.lark.schemas import LarkMessage
from app.integrations.lark.service import LarkService, get_lark_service
from app.orchestrator.dialog_state import DialogStateMachine, get_dialog_state_machine
from app.orchestrator.intent_router import IntentRouterV2, get_intent_router_v2
from app.orchestrator.schemas import (
    DialogSession,
    DialogState,
    IntentResult,
    IntentType,
    SkillExecutionContext,
    SkillExecutionResult,
    UserContext,
)
from app.orchestrator.skill_registry import SkillRegistry, get_skill_registry
from app.services.access_control_service import AccessControlService
from app.services.audit_service import AuditService
from app.services.context_service import ContextService, get_context_service

logger = get_logger(__name__)


class Orchestrator:
    """
    主编排引擎.

    协调意图识别、状态流转、Skill执行、结果展示。
    """

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """
        初始化编排引擎.

        Args:
            session: 数据库会话
        """
        self._session = session
        self._context_service = get_context_service()
        self._intent_router = get_intent_router_v2()
        self._dialog_state_machine = get_dialog_state_machine()
        self._skill_registry = get_skill_registry()
        self._lark_service = get_lark_service()

    async def process_message(
        self,
        message: LarkMessage,
        sender_open_id: str,
        trace_id: Optional[str] = None,
    ) -> SkillExecutionResult:
        """
        处理飞书消息.

        完整的消息处理流程：上下文构建 -> 意图识别 -> 状态流转 -> Skill执行。

        Args:
            message: 飞书消息对象
            sender_open_id: 发送者OpenID
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        trace_id = trace_id or str(uuid.uuid4())

        logger.info(
            "Processing message",
            trace_id=trace_id,
            message_id=message.message_id,
            chat_id=message.chat_id,
            sender_open_id=sender_open_id,
        )

        # 构建用户上下文
        user_context = await self._build_user_context(
            sender_open_id,
            message.chat_id,
            message.chat_type or "p2p",
        )

        # 获取或创建对话会话
        dialog_session = await self._dialog_state_machine.get_or_create_session(
            user_id=sender_open_id,
            chat_id=message.chat_id,
            project_id=user_context.current_project,
        )

        # 解析消息内容
        content = self._parse_message_content(message)

        # 根据当前状态处理
        if dialog_session.state == DialogState.PARAM_COLLECTING:
            # 参数收集阶段
            return await self._handle_param_collection(
                dialog_session,
                content,
                trace_id,
            )

        if dialog_session.state == DialogState.CONFIRMATION_PENDING:
            # 确认等待阶段
            return await self._handle_confirmation(
                dialog_session,
                content,
                trace_id,
            )

        if dialog_session.state == DialogState.EXECUTING:
            # 执行中阶段（不应该收到新消息）
            logger.warning(
                "Received message while executing",
                trace_id=trace_id,
                session_id=dialog_session.session_id,
            )
            return SkillExecutionResult(
                success=False,
                skill_name="",
                error_message="正在执行中，请稍候...",
            )

        # 新意图识别
        return await self._handle_new_intent(
            dialog_session,
            content,
            user_context,
            trace_id,
        )

    async def _build_user_context(
        self,
        sender_open_id: str,
        chat_id: str,
        chat_type: str,
    ) -> UserContext:
        """
        构建用户上下文.

        Args:
            sender_open_id: 发送者OpenID
            chat_id: 会话ID
            chat_type: 会话类型

        Returns:
            UserContext: 用户上下文
        """
        # 使用上下文服务构建
        context = await self._context_service.build_user_context(
            feishu_user_id=sender_open_id,
            chat_id=chat_id,
            chat_type=chat_type,
        )

        return context

    async def _handle_new_intent(
        self,
        dialog_session: DialogSession,
        content: str,
        user_context: UserContext,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        处理新意图.

        Args:
            dialog_session: 对话会话
            content: 消息内容
            user_context: 用户上下文
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 获取可用Skill列表
        available_skills = await self._get_available_skills(user_context)

        # 意图识别
        intent_result = await self._intent_router.recognize_with_context(
            user_message=content,
            user_context=user_context,
            conversation_history=dialog_session.conversation_messages,
            available_skills=available_skills,
        )

        # 更新对话历史
        dialog_session.conversation_messages.append({
            "role": "user",
            "content": content,
        })

        # 根据意图类型处理
        if intent_result.intent_type == IntentType.REJECTION:
            # 拒绝执行
            return self._build_rejection_result(intent_result)

        if intent_result.intent_type == IntentType.UNKNOWN:
            # 未知意图
            return self._build_unknown_intent_result(content)

        if intent_result.intent_type in (IntentType.CLARIFICATION, IntentType.AMBIGUOUS):
            # 需要澄清
            return await self._handle_clarification(
                dialog_session,
                intent_result,
                trace_id,
            )

        if intent_result.intent_type == IntentType.SKILL_EXECUTION:
            # Skill执行意图
            return await self._handle_skill_execution_intent(
                dialog_session,
                intent_result,
                user_context,
                trace_id,
            )

        return SkillExecutionResult(
            success=False,
            skill_name="",
            error_message="无法处理的消息",
        )

    async def _handle_skill_execution_intent(
        self,
        dialog_session: DialogSession,
        intent_result: IntentResult,
        user_context: UserContext,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        处理Skill执行意图.

        Args:
            dialog_session: 对话会话
            intent_result: 意图结果
            user_context: 用户上下文
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        skill_name = intent_result.matched_skill

        if not skill_name:
            return SkillExecutionResult(
                success=False,
                skill_name="",
                error_message="未匹配到具体功能",
            )

        # 获取Skill Manifest
        try:
            manifest = self._skill_registry.get_manifest(skill_name)
        except SkillNotFoundError:
            return SkillExecutionResult(
                success=False,
                skill_name=skill_name,
                error_message=f"功能 {skill_name} 不存在",
            )

        # 检查权限
        if self._session:
            access_control = AccessControlService(self._session)
            has_permission = await access_control.check_skill_access(
                user_id=user_context.user_id,
                project_id=user_context.current_project,
                skill_name=skill_name,
                user_role=user_context.user_role,
            )
            if not has_permission:
                return SkillExecutionResult(
                    success=False,
                    skill_name=skill_name,
                    error_message="您没有权限执行此功能",
                )

        # 状态流转
        dialog_session = await self._dialog_state_machine.transition(
            dialog_session,
            intent_result,
            manifest,
        )

        # 根据状态执行
        if dialog_session.state == DialogState.PARAM_COLLECTING:
            # 需要收集参数
            return await self._request_param_collection(
                dialog_session,
                manifest,
                trace_id,
            )

        if dialog_session.state == DialogState.CONFIRMATION_PENDING:
            # 需要确认
            return await self._request_confirmation(
                dialog_session,
                manifest,
                trace_id,
            )

        if dialog_session.state == DialogState.EXECUTING:
            # 可以执行
            return await self._execute_skill(
                dialog_session,
                manifest,
                user_context,
                trace_id,
            )

        return SkillExecutionResult(
            success=False,
            skill_name=skill_name,
            error_message="状态异常，无法执行",
        )

    async def _handle_param_collection(
        self,
        dialog_session: DialogSession,
        content: str,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        处理参数收集.

        Args:
            dialog_session: 对话会话
            content: 用户输入内容
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        if not dialog_session.missing_params:
            # 无缺失参数，直接执行
            return await self._execute_with_collected_params(
                dialog_session,
                trace_id,
            )

        # 收集第一个缺失参数
        first_missing = dialog_session.missing_params[0]

        # 更新对话历史
        dialog_session.conversation_messages.append({
            "role": "user",
            "content": content,
        })

        # 收集参数
        dialog_session = await self._dialog_state_machine.collect_param(
            dialog_session,
            first_missing,
            content,
        )

        # 检查是否还有缺失参数
        if dialog_session.missing_params:
            # 继续收集
            manifest = self._skill_registry.get_manifest(
                dialog_session.current_skill,
            )
            return await self._request_param_collection(
                dialog_session,
                manifest,
                trace_id,
            )

        # 参数收集完成，检查是否需要确认
        manifest = self._skill_registry.get_manifest(dialog_session.current_skill)

        if manifest.supports_confirmation:
            dialog_session.state = DialogState.CONFIRMATION_PENDING
            await self._dialog_state_machine.update_session(dialog_session)
            return await self._request_confirmation(
                dialog_session,
                manifest,
                trace_id,
            )

        # 直接执行
        return await self._execute_with_collected_params(
            dialog_session,
            trace_id,
        )

    async def _handle_confirmation(
        self,
        dialog_session: DialogSession,
        content: str,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        处理确认响应.

        Args:
            dialog_session: 对话会话
            content: 用户输入内容
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 判断用户是否确认
        confirmed = self._parse_confirmation(content)

        # 更新对话历史
        dialog_session.conversation_messages.append({
            "role": "user",
            "content": content,
        })

        # 处理确认
        dialog_session = await self._dialog_state_machine.confirm_execution(
            dialog_session,
            confirmed,
        )

        if confirmed:
            # 执行Skill
            return await self._execute_with_collected_params(
                dialog_session,
                trace_id,
            )
        else:
            # 用户取消
            return SkillExecutionResult(
                success=True,
                skill_name=dialog_session.current_skill or "",
                presentation_type="text",
                presentation_data={"text": "操作已取消"},
            )

    async def _handle_clarification(
        self,
        dialog_session: DialogSession,
        intent_result: IntentResult,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        处理澄清请求.

        Args:
            dialog_session: 对话会话
            intent_result: 意图结果
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 澄清卡片结果
        """
        # 发送澄清卡片
        if intent_result.matched_skill and intent_result.confidence > 0.5:
            # 有一个主要候选
            manifest = self._skill_registry.get_manifest(
                intent_result.matched_skill,
            )

            card = self._build_clarification_card(
                matched_skill=manifest.skill_name,
                skill_description=manifest.display_name,
                confidence=intent_result.confidence,
            )

            return SkillExecutionResult(
                success=True,
                skill_name="clarification",
                requires_confirmation=True,
                confirmation_card=card,
            )
        else:
            # 多个候选
            return self._build_ambiguous_result(intent_result)

    async def _request_param_collection(
        self,
        dialog_session: DialogSession,
        manifest: Any,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        请求参数收集.

        Args:
            dialog_session: 对话会话
            manifest: Skill Manifest
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 参数请求结果
        """
        prompt = self._dialog_state_machine.generate_param_prompt(
            dialog_session,
            manifest,
        )

        return SkillExecutionResult(
            success=True,
            skill_name=manifest.skill_name,
            presentation_type="text",
            presentation_data={
                "text": prompt.prompt_message,
            },
        )

    async def _request_confirmation(
        self,
        dialog_session: DialogSession,
        manifest: Any,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        请求执行确认.

        Args:
            dialog_session: 对话会话
            manifest: Skill Manifest
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 确认请求结果
        """
        card = self._build_confirmation_card(
            skill_name=manifest.skill_name,
            skill_display_name=manifest.display_name,
            params=dialog_session.collected_params,
        )

        return SkillExecutionResult(
            success=True,
            skill_name=manifest.skill_name,
            requires_confirmation=True,
            confirmation_card=card,
        )

    async def _execute_skill(
        self,
        dialog_session: DialogSession,
        manifest: Any,
        user_context: UserContext,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        执行Skill.

        Args:
            dialog_session: 对话会话
            manifest: Skill Manifest
            user_context: 用户上下文
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        # 标记为执行中
        dialog_session = await self._dialog_state_machine.mark_executing(
            dialog_session,
        )

        # 构建执行上下文
        execution_context = SkillExecutionContext(
            trace_id=trace_id,
            user_id=user_context.user_id,
            chat_id=user_context.chat_id,
            chat_type=user_context.chat_type,
            project_id=user_context.current_project,
            user_role=user_context.user_role,
            skill_name=manifest.skill_name,
            params=dialog_session.collected_params,
            conversation_history=dialog_session.conversation_messages,
        )

        # 获取Skill类
        skill_class = self._skill_registry.get_skill_class(manifest.skill_name)

        if skill_class is None:
            # Skill未实现
            return SkillExecutionResult(
                success=False,
                skill_name=manifest.skill_name,
                error_message=f"功能 {manifest.display_name} 暂未实现",
            )

        # 执行Skill
        try:
            skill_instance = skill_class(
                manifest=manifest,
                context=execution_context,
                session=self._session,
            )

            result = await skill_instance.execute()

            # 标记完成
            dialog_session = await self._dialog_state_machine.mark_completed(
                dialog_session,
                result,
            )

            # 记录审计日志
            if self._session:
                audit_service = AuditService(self._session)
                await audit_service.log_skill_execution(
                    user_id=user_context.user_id,
                    skill_name=manifest.skill_name,
                    trace_id=trace_id,
                    project_id=user_context.current_project,
                    params=dialog_session.collected_params,
                    result=result.success and "success" or "failed",
                    duration_ms=result.duration_ms,
                    error_message=result.error_message,
                )

            return result

        except Exception as e:
            logger.error(
                "Skill execution failed",
                trace_id=trace_id,
                skill_name=manifest.skill_name,
                error=str(e),
            )

            # 标记失败
            result = SkillExecutionResult(
                success=False,
                skill_name=manifest.skill_name,
                error_message=str(e),
            )

            dialog_session = await self._dialog_state_machine.mark_completed(
                dialog_session,
                result,
            )

            return result

    async def _execute_with_collected_params(
        self,
        dialog_session: DialogSession,
        trace_id: str,
    ) -> SkillExecutionResult:
        """
        使用已收集的参数执行Skill.

        Args:
            dialog_session: 对话会话
            trace_id: 追踪ID

        Returns:
            SkillExecutionResult: 执行结果
        """
        skill_name = dialog_session.current_skill

        if not skill_name:
            return SkillExecutionResult(
                success=False,
                skill_name="",
                error_message="未指定功能",
            )

        manifest = self._skill_registry.get_manifest(skill_name)

        # 构建用户上下文（简化）
        user_context = UserContext(
            user_id=dialog_session.user_id,
            chat_id=dialog_session.chat_id,
            chat_type="p2p",
            current_project=dialog_session.project_id,
        )

        return await self._execute_skill(
            dialog_session,
            manifest,
            user_context,
            trace_id,
        )

    async def _get_available_skills(
        self,
        user_context: UserContext,
    ) -> Optional[list]:
        """
        获取可用Skill列表.

        Args:
            user_context: 用户上下文

        Returns:
            Optional[list]: Skill名称列表
        """
        if self._session:
            manifests = await self._skill_registry.get_available_skills_for_user(
                user_context,
            )
            return [m.skill_name for m in manifests]

        # 无数据库时返回所有
        return None

    def _parse_message_content(
        self,
        message: LarkMessage,
    ) -> str:
        """
        解析消息内容.

        Args:
            message: 飞书消息

        Returns:
            str: 消息内容
        """
        import json

        if message.message_type == "text":
            try:
                content_dict = json.loads(message.content or "{}")
                return content_dict.get("text", "")
            except json.JSONDecodeError:
                return message.content or ""

        # 其他类型暂不支持
        return message.content or ""

    def _parse_confirmation(
        self,
        content: str,
    ) -> bool:
        """
        解析确认响应.

        Args:
            content: 用户输入

        Returns:
            bool: 是否确认
        """
        positive_keywords = [
            "确认", "是", "执行", "好的", "ok", "OK",
            "同意", "没问题", "可以",
        ]
        negative_keywords = [
            "取消", "不", "否", "拒绝", "放弃",
            "算了", "不要", "不行",
        ]

        content_lower = content.lower()

        for keyword in positive_keywords:
            if keyword in content_lower:
                return True

        for keyword in negative_keywords:
            if keyword in content_lower:
                return False

        # 默认不确认
        return False

    def _build_rejection_result(
        self,
        intent_result: IntentResult,
    ) -> SkillExecutionResult:
        """
        构建拒绝结果.

        Args:
            intent_result: 意图结果

        Returns:
            SkillExecutionResult: 拒绝结果
        """
        return SkillExecutionResult(
            success=False,
            skill_name="",
            error_message=intent_result.rejection_reason or "请求被拒绝",
        )

    def _build_unknown_intent_result(
        self,
        content: str,
    ) -> SkillExecutionResult:
        """
        构建未知意图结果.

        Args:
            content: 用户输入

        Returns:
            SkillExecutionResult: 未知意图结果
        """
        return SkillExecutionResult(
            success=False,
            skill_name="",
            presentation_type="text",
            presentation_data={
                "text": "抱歉，我无法理解您的请求。您可以尝试：\n"
                "- 查看项目状态\n"
                "- 生成周报\n"
                "- 更新任务进度\n"
                "- 查看风险",
            },
        )

    def _build_ambiguous_result(
        self,
        intent_result: IntentResult,
    ) -> SkillExecutionResult:
        """
        构建模糊意图结果.

        Args:
            intent_result: 意图结果

        Returns:
            SkillExecutionResult: 澄清结果
        """
        candidates = intent_result.candidate_skills

        text = "您可能想要执行以下功能之一：\n\n"
        for i, candidate in enumerate(candidates[:3], 1):
            skill_name = candidate.get("skill_name", "")
            skill_desc = candidate.get("description", "")
            text += f"{i}. {skill_desc}\n"

        text += "\n请回复序号或详细描述您的需求。"

        return SkillExecutionResult(
            success=True,
            skill_name="clarification",
            presentation_type="text",
            presentation_data={"text": text},
        )

    def _build_clarification_card(
        self,
        matched_skill: str,
        skill_description: str,
        confidence: float,
    ) -> Dict[str, Any]:
        """
        构建澄清卡片.

        Args:
            matched_skill: 匹配的Skill
            skill_description: Skill描述
            confidence: 置信度

        Returns:
            Dict: 卡片内容
        """
        from app.integrations.lark.schemas import LarkCardBuilder

        card = (
            LarkCardBuilder()
            .set_header("请确认您的意图", "blue")
            .add_markdown(
                f"检测到您可能想要：**{skill_description}**\n\n"
                f"置信度: {confidence:.0%}\n\n"
                f"是否确认执行？",
            )
            .add_divider()
            .add_action(
                [
                    LarkCardBuilder.create_button(
                        "确认执行",
                        {"action": "confirm", "skill": matched_skill},
                        "primary",
                    ),
                    LarkCardBuilder.create_button(
                        "取消",
                        {"action": "cancel"},
                        "default",
                    ),
                ],
            )
            .build()
        )

        return card

    def _build_confirmation_card(
        self,
        skill_name: str,
        skill_display_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        构建确认卡片.

        Args:
            skill_name: Skill名称
            skill_display_name: Skill显示名
            params: 执行参数

        Returns:
            Dict: 卡片内容
        """
        from app.integrations.lark.schemas import LarkCardBuilder

        # 构建参数展示
        params_text = "执行参数：\n"
        for key, value in params.items():
            params_text += f"- {key}: {value}\n"

        card = (
            LarkCardBuilder()
            .set_header(f"确认执行：{skill_display_name}", "blue")
            .add_markdown(params_text)
            .add_divider()
            .add_markdown("请确认是否执行此操作？")
            .add_action(
                [
                    LarkCardBuilder.create_button(
                        "确认执行",
                        {"action": "confirm", "skill": skill_name},
                        "primary",
                    ),
                    LarkCardBuilder.create_button(
                        "取消",
                        {"action": "cancel"},
                        "default",
                    ),
                ],
            )
            .build()
        )

        return card


# 全局编排器实例
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """获取编排器实例."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def init_orchestrator(session: AsyncSession) -> Orchestrator:
    """初始化编排器（带数据库会话）."""
    global _orchestrator
    _orchestrator = Orchestrator(session=session)
    return _orchestrator