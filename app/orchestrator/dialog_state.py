"""
PM Digital Employee - Dialog State Machine
项目经理数字员工系统 - 多轮对话状态机

管理多轮对话状态流转，处理参数收集、确认流程、异常恢复。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.exceptions import DialogSessionError
from app.core.logging import get_logger
from app.orchestrator.schemas import (
    DialogSession,
    DialogState,
    IntentResult,
    IntentType,
    ParamCollectionPrompt,
    SkillExecutionContext,
    SkillExecutionResult,
    SkillManifest,
)

logger = get_logger(__name__)


class DialogStateMachine:
    """
    多轮对话状态机.

    管理对话状态流转、参数收集、确认流程。
    使用Redis存储会话状态，支持跨请求持久化。
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        """
        初始化状态机.

        Args:
            redis_client: Redis客户端
        """
        self._redis = redis_client
        self._key_prefix = "dialog:session:"
        self._session_ttl = 30 * 60  # 30分钟会话过期

    async def _get_redis(self) -> redis.Redis:
        """获取Redis客户端."""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                decode_responses=True,
            )
        return self._redis

    async def create_session(
        self,
        user_id: str,
        chat_id: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> DialogSession:
        """
        创建新对话会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID
            project_id: 项目ID

        Returns:
            DialogSession: 新会话对象
        """
        session = DialogSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            chat_id=chat_id,
            project_id=project_id,
            state=DialogState.IDLE,
        )

        await self._save_session(session)

        logger.info(
            "Dialog session created",
            session_id=session.session_id,
            user_id=user_id,
            chat_id=chat_id,
        )

        return session

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[DialogSession]:
        """
        获取会话状态.

        Args:
            session_id: 会话ID

        Returns:
            Optional[DialogSession]: 会话对象或None
        """
        redis_client = await self._get_redis()
        key = self._build_key(session_id)

        data = await redis_client.get(key)
        if data:
            import json
            session_dict = json.loads(data)
            return DialogSession.model_validate(session_dict)

        return None

    async def get_or_create_session(
        self,
        user_id: str,
        chat_id: str,
        project_id: Optional[uuid.UUID] = None,
    ) -> DialogSession:
        """
        获取或创建会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID
            project_id: 项目ID

        Returns:
            DialogSession: 会话对象
        """
        # 尝试获取现有会话
        existing_session = await self._find_active_session(user_id, chat_id)
        if existing_session:
            return existing_session

        # 创建新会话
        return await self.create_session(user_id, chat_id, project_id)

    async def update_session(
        self,
        session: DialogSession,
    ) -> None:
        """
        更新会话状态.

        Args:
            session: 会话对象
        """
        session.updated_at = datetime.now(timezone.utc)
        await self._save_session(session)

    async def end_session(
        self,
        session_id: str,
    ) -> bool:
        """
        结束会话.

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功结束
        """
        redis_client = await self._get_redis()
        key = self._build_key(session_id)

        result = await redis_client.delete(key)

        logger.info(
            "Dialog session ended",
            session_id=session_id,
        )

        return result > 0

    async def transition(
        self,
        session: DialogSession,
        intent_result: IntentResult,
        manifest: Optional[SkillManifest] = None,
    ) -> DialogSession:
        """
        状态流转.

        根据意图识别结果更新会话状态。

        Args:
            session: 当前会话
            intent_result: 意图识别结果
            manifest: Skill Manifest

        Returns:
            DialogSession: 更新后的会话
        """
        new_state = self._calculate_new_state(session, intent_result, manifest)

        session.state = new_state
        session.intent_result = intent_result

        if intent_result.matched_skill:
            session.current_skill = intent_result.matched_skill

        if intent_result.extracted_params:
            # 合并参数
            session.collected_params.update(intent_result.extracted_params)

        if intent_result.missing_params:
            session.missing_params = intent_result.missing_params
        else:
            # 检查Manifest中定义的必填参数
            if manifest:
                required_params = manifest.input_schema.get("required", [])
                missing = [
                    p for p in required_params
                    if p not in session.collected_params
                ]
                session.missing_params = missing

        await self.update_session(session)

        logger.info(
            "Dialog state transitioned",
            session_id=session.session_id,
            previous_state=session.state,
            new_state=new_state,
            current_skill=session.current_skill,
        )

        return session

    def _calculate_new_state(
        self,
        session: DialogSession,
        intent_result: IntentResult,
        manifest: Optional[SkillManifest],
    ) -> DialogState:
        """
        计算新状态.

        Args:
            session: 当前会话
            intent_result: 意图结果
            manifest: Skill Manifest

        Returns:
            DialogState: 新状态
        """
        current_state = session.state

        # 根据意图类型确定新状态
        if intent_result.intent_type == IntentType.REJECTION:
            return DialogState.CANCELLED

        if intent_result.intent_type == IntentType.UNKNOWN:
            return DialogState.IDLE

        if intent_result.intent_type == IntentType.CLARIFICATION:
            return DialogState.INTENT_RECOGNIZED

        if intent_result.intent_type == IntentType.AMBIGUOUS:
            return DialogState.INTENT_RECOGNIZED

        if intent_result.intent_type == IntentType.SKILL_EXECUTION:
            # 检查是否有缺失参数
            if intent_result.missing_params:
                return DialogState.PARAM_COLLECTING

            # 检查是否需要确认
            if manifest and manifest.supports_confirmation:
                return DialogState.CONFIRMATION_PENDING

            # 可以直接执行
            return DialogState.EXECUTING

        # 默认保持当前状态
        return current_state

    async def collect_param(
        self,
        session: DialogSession,
        param_name: str,
        param_value: Any,
    ) -> DialogSession:
        """
        收集参数.

        Args:
            session: 当前会话
            param_name: 参数名
            param_value: 参数值

        Returns:
            DialogSession: 更新后的会话
        """
        session.collected_params[param_name] = param_value

        # 从缺失列表中移除
        if param_name in session.missing_params:
            session.missing_params.remove(param_name)

        # 判断是否可以进入下一状态
        if not session.missing_params:
            # 参数收集完成
            manifest = await self._get_skill_manifest(session.current_skill)
            if manifest and manifest.supports_confirmation:
                session.state = DialogState.CONFIRMATION_PENDING
            else:
                session.state = DialogState.EXECUTING
        else:
            # 继续收集参数
            session.state = DialogState.PARAM_COLLECTING

        await self.update_session(session)

        logger.debug(
            "Parameter collected",
            session_id=session.session_id,
            param_name=param_name,
            remaining_params=session.missing_params,
        )

        return session

    async def confirm_execution(
        self,
        session: DialogSession,
        confirmed: bool,
    ) -> DialogSession:
        """
        处理确认响应.

        Args:
            session: 当前会话
            confirmed: 是否确认执行

        Returns:
            DialogSession: 更新后的会话
        """
        if confirmed:
            session.state = DialogState.EXECUTING
        else:
            session.state = DialogState.CANCELLED
            session.current_skill = None
            session.collected_params = {}
            session.missing_params = []

        await self.update_session(session)

        logger.info(
            "Execution confirmation processed",
            session_id=session.session_id,
            confirmed=confirmed,
        )

        return session

    async def mark_executing(
        self,
        session: DialogSession,
    ) -> DialogSession:
        """
        标记为执行中.

        Args:
            session: 当前会话

        Returns:
            DialogSession: 更新后的会话
        """
        session.state = DialogState.EXECUTING
        await self.update_session(session)
        return session

    async def mark_completed(
        self,
        session: DialogSession,
        result: SkillExecutionResult,
    ) -> DialogSession:
        """
        标记执行完成.

        Args:
            session: 当前会话
            result: 执行结果

        Returns:
            DialogSession: 更新后的会话
        """
        if result.success:
            session.state = DialogState.COMPLETED
        else:
            session.state = DialogState.FAILED

        session.execution_result = result

        await self.update_session(session)

        logger.info(
            "Execution completed",
            session_id=session.session_id,
            success=result.success,
        )

        return session

    async def reset_session(
        self,
        session: DialogSession,
    ) -> DialogSession:
        """
        重置会话状态.

        Args:
            session: 当前会话

        Returns:
            DialogSession: 重置后的会话
        """
        session.state = DialogState.IDLE
        session.current_skill = None
        session.collected_params = {}
        session.missing_params = []
        session.intent_result = None
        session.execution_result = None

        await self.update_session(session)

        logger.info(
            "Session reset",
            session_id=session.session_id,
        )

        return session

    def generate_param_prompt(
        self,
        session: DialogSession,
        manifest: SkillManifest,
    ) -> ParamCollectionPrompt:
        """
        生成参数收集提示.

        Args:
            session: 当前会话
            manifest: Skill Manifest

        Returns:
            ParamCollectionPrompt: 参数收集提示
        """
        if not session.missing_params:
            raise DialogSessionError(
                message="No missing parameters to collect",
            )

        # 取第一个缺失参数
        missing_param = session.missing_params[0]
        param_schema = manifest.input_schema.get("properties", {}).get(
            missing_param, {},
        )

        return ParamCollectionPrompt(
            missing_param=missing_param,
            param_description=param_schema.get("description", missing_param),
            param_type=param_schema.get("type", "string"),
            examples=param_schema.get("examples", []),
            prompt_message=self._build_param_prompt_message(
                missing_param,
                param_schema,
                manifest.display_name,
            ),
        )

    def _build_param_prompt_message(
        self,
        param_name: str,
        param_schema: Dict[str, Any],
        skill_display_name: str,
    ) -> str:
        """
        构建参数提示消息.

        Args:
            param_name: 参数名
            param_schema: 参数Schema
            skill_display_name: Skill显示名

        Returns:
            str: 提示消息
        """
        description = param_schema.get("description", param_name)
        examples = param_schema.get("examples", [])
        param_type = param_schema.get("type", "string")

        message = f"执行 **{skill_display_name}** 需要以下信息：\n\n"
        message += f"请提供 **{description}**"

        if examples:
            message += f"\n示例：{', '.join(examples[:3])}"

        if param_schema.get("enum"):
            message += f"\n可选值：{', '.join(param_schema['enum'])}"

        return message

    async def _save_session(
        self,
        session: DialogSession,
    ) -> None:
        """
        保存会话到Redis.

        Args:
            session: 会话对象
        """
        redis_client = await self._get_redis()
        key = self._build_key(session.session_id)

        import json
        data = json.dumps(
            session.model_dump(exclude_none=True),
            ensure_ascii=False,
        )

        await redis_client.set(key, data, ex=self._session_ttl)

    async def _find_active_session(
        self,
        user_id: str,
        chat_id: str,
    ) -> Optional[DialogSession]:
        """
        查找活跃会话.

        Args:
            user_id: 用户ID
            chat_id: 会话ID

        Returns:
            Optional[DialogSession]: 活跃会话
        """
        # 简化实现：通过用户-会话映射查找
        redis_client = await self._get_redis()
        mapping_key = f"dialog:mapping:{user_id}:{chat_id}"

        session_id = await redis_client.get(mapping_key)
        if session_id:
            return await self.get_session(session_id)

        return None

    async def _get_skill_manifest(
        self,
        skill_name: Optional[str],
    ) -> Optional[SkillManifest]:
        """
        获取Skill Manifest.

        Args:
            skill_name: Skill名称

        Returns:
            Optional[SkillManifest]: Manifest对象
        """
        if not skill_name:
            return None

        from app.orchestrator.skill_registry import get_skill_registry

        registry = get_skill_registry()
        try:
            return registry.get_manifest(skill_name)
        except Exception:
            return None

    def _build_key(self, session_id: str) -> str:
        """构建Redis key."""
        return f"{self._key_prefix}{session_id}"


# 全局状态机实例
_dialog_state_machine: Optional[DialogStateMachine] = None


def get_dialog_state_machine() -> DialogStateMachine:
    """获取状态机实例."""
    global _dialog_state_machine
    if _dialog_state_machine is None:
        _dialog_state_machine = DialogStateMachine()
    return _dialog_state_machine


def init_dialog_state_machine(redis_client: redis.Redis) -> DialogStateMachine:
    """初始化状态机（带Redis客户端）."""
    global _dialog_state_machine
    _dialog_state_machine = DialogStateMachine(redis_client=redis_client)
    return _dialog_state_machine