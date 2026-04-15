"""
PM Digital Employee - Intent Router
项目经理数字员工系统 - 意图识别与路由引擎

基于LLM进行用户意图识别，匹配对应的Skill，提取执行参数。
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from app.ai.llm_gateway import get_llm_gateway
from app.ai.output_parser import StructuredOutputParser
from app.ai.safety_guard import get_safety_guard
from app.core.config import settings
from app.core.exceptions import ErrorCode, IntentRecognitionError
from app.core.logging import get_logger
from app.orchestrator.schemas import (
    IntentRecognitionRequest,
    IntentResult,
    IntentType,
    UserContext,
)
from app.orchestrator.skill_registry import get_skill_registry

logger = get_logger(__name__)


# 意图识别Prompt模板
INTENT_RECOGNITION_PROMPT = """你是一个项目经理数字员工的意图识别助手。

## 任务
分析用户的输入，判断用户想要执行什么操作，并匹配到对应的Skill。

## 可用Skill列表
{skill_descriptions}

## 用户上下文
- 用户角色: {user_role}
- 当前项目: {project_name}
- 会话类型: {chat_type}

## 用户输入
{user_message}

## 对话历史
{conversation_history}

## 输出要求
请以JSON格式输出分析结果，包含以下字段：
- intent_type: 意图类型，取值: "skill_execution"(Skill执行), "clarification"(需要澄清), "ambiguous"(多个候选), "unknown"(未知意图), "rejection"(拒绝执行)
- matched_skill: 匹配的Skill名称（skill_execution时必填）
- skill_description: Skill的中文描述
- confidence: 置信度（0-1之间的浮点数）
- candidate_skills: 候选Skill列表（confidence<0.7时列出可能的候选）
- extracted_params: 从用户输入中提取的参数
- missing_params: 缺失的必填参数列表
- rejection_reason: 拒绝原因（rejection时填写）

## 示例输出
```json
{
  "intent_type": "skill_execution",
  "matched_skill": "project_overview",
  "skill_description": "查询项目整体状态信息",
  "confidence": 0.95,
  "extracted_params": {"project_id": "项目A"},
  "missing_params": []
}
```

请直接输出JSON，不要包含其他内容。
"""


class IntentRouter:
    """
    意图识别与路由引擎.

    基于LLM分析用户输入，识别意图，匹配Skill，提取参数。
    """

    def __init__(self) -> None:
        """初始化意图路由器."""
        self._llm_gateway = get_llm_gateway()
        self._safety_guard = get_safety_guard()
        self._output_parser = StructuredOutputParser()
        self._skill_registry = get_skill_registry()

    async def recognize(
        self,
        request: IntentRecognitionRequest,
    ) -> IntentResult:
        """
        识别用户意图.

        Args:
            request: 意图识别请求

        Returns:
            IntentResult: 意图识别结果

        Raises:
            IntentRecognitionError: 意图识别失败
        """
        start_time = time.time()

        # 安全检查：检测提示词注入
        safety_result = await self._safety_guard.check_prompt_injection(
            request.user_message,
        )

        if safety_result.is_malicious:
            logger.warning(
                "Prompt injection detected",
                user_id=request.user_id,
                risk_level=safety_result.risk_level,
            )
            return IntentResult(
                intent_type=IntentType.REJECTION,
                rejection_reason="检测到异常输入，请求已拒绝",
                raw_response=safety_result.explanation,
            )

        # 获取可用Skill描述
        skill_descriptions = self._build_skill_descriptions(
            request.available_skills,
        )

        # 构建Prompt
        prompt = INTENT_RECOGNITION_PROMPT.format(
            skill_descriptions=skill_descriptions,
            user_role=request.chat_type,  # 简化处理
            project_name="当前项目",  # TODO: 从上下文获取实际项目名
            chat_type=request.chat_type,
            user_message=request.user_message,
            conversation_history=self._format_history(
                request.conversation_history,
            ),
        )

        # 调用LLM
        try:
            llm_result = await self._llm_gateway.generate(
                prompt=prompt,
                model=settings.llm.intent_model,
                max_tokens=settings.llm.intent_max_tokens,
                temperature=settings.llm.intent_temperature,
            )

            # 解析结构化输出
            parsed_result = self._parse_llm_response(
                llm_result.content,
            )

            # 构建IntentResult
            intent_result = IntentResult(
                intent_type=self._map_intent_type(
                    parsed_result.get("intent_type", "unknown"),
                ),
                matched_skill=parsed_result.get("matched_skill"),
                skill_description=parsed_result.get("skill_description"),
                confidence=parsed_result.get("confidence", 0.0),
                candidate_skills=parsed_result.get("candidate_skills", []),
                extracted_params=parsed_result.get("extracted_params", {}),
                missing_params=parsed_result.get("missing_params", []),
                rejection_reason=parsed_result.get("rejection_reason"),
                raw_response=llm_result.content,
                tokens_used=llm_result.total_tokens,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Intent recognized",
                user_id=request.user_id,
                intent_type=intent_result.intent_type,
                matched_skill=intent_result.matched_skill,
                confidence=intent_result.confidence,
                duration_ms=duration_ms,
                tokens_used=intent_result.tokens_used,
            )

            return intent_result

        except Exception as e:
            logger.error(
                "Intent recognition failed",
                user_id=request.user_id,
                error=str(e),
            )
            raise IntentRecognitionError(
                message=f"意图识别失败: {str(e)}",
            )

    def _build_skill_descriptions(
        self,
        available_skills: List[str],
    ) -> str:
        """
        构建Skill描述列表.

        Args:
            available_skills: 可用Skill名称列表

        Returns:
            str: 格式化的Skill描述
        """
        descriptions = self._skill_registry.get_skill_descriptions()
        display_names = self._skill_registry.get_skill_display_names()

        lines: List[str] = []

        if available_skills:
            for skill_name in available_skills:
                if skill_name in descriptions:
                    display_name = display_names.get(skill_name, skill_name)
                    description = descriptions[skill_name]
                    lines.append(f"- **{skill_name}** ({display_name}): {description}")
        else:
            # 使用所有注册的Skill
            for skill_name, description in descriptions.items():
                display_name = display_names.get(skill_name, skill_name)
                lines.append(f"- **{skill_name}** ({display_name}): {description}")

        return "\n".join(lines)

    def _format_history(
        self,
        history: List[Dict[str, str]],
    ) -> str:
        """
        格式化对话历史.

        Args:
            history: 对话历史列表

        Returns:
            str: 格式化的历史
        """
        if not history:
            return "无历史对话"

        lines: List[str] = []
        for msg in history[-5:]:  # 最多取最近5条
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            elif role == "assistant":
                lines.append(f"助手: {content}")

        return "\n".join(lines) if lines else "无历史对话"

    def _parse_llm_response(
        self,
        response: str,
    ) -> Dict[str, Any]:
        """
        解析LLM响应.

        Args:
            response: LLM原始响应

        Returns:
            Dict: 解析后的结果
        """
        # 尝试提取JSON
        try:
            # 尝试直接解析
            if response.strip().startswith("{"):
                return json.loads(response.strip())

            # 尝试提取JSON块
            json_match = self._output_parser.extract_json(response)
            if json_match:
                return json.loads(json_match)

            logger.warning(
                "Failed to extract JSON from LLM response",
                response_preview=response[:200],
            )
            return {"intent_type": "unknown"}

        except json.JSONDecodeError as e:
            logger.error(
                "JSON decode error",
                error=str(e),
                response_preview=response[:200],
            )
            return {"intent_type": "unknown"}

    def _map_intent_type(
        self,
        type_str: str,
    ) -> IntentType:
        """
        映射意图类型字符串.

        Args:
            type_str: 类型字符串

        Returns:
            IntentType: 意图类型枚举
        """
        mapping = {
            "skill_execution": IntentType.SKILL_EXECUTION,
            "clarification": IntentType.CLARIFICATION,
            "ambiguous": IntentType.AMBIGUOUS,
            "unknown": IntentType.UNKNOWN,
            "rejection": IntentType.REJECTION,
        }
        return mapping.get(type_str.lower(), IntentType.UNKNOWN)

    async def quick_match(
        self,
        user_message: str,
        available_skills: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        快速关键词匹配.

        用于简单场景的关键词匹配，不调用LLM。

        Args:
            user_message: 用户消息
            available_skills: 可用Skill列表

        Returns:
            Optional[str]: 匹配的Skill名称或None
        """
        # 关键词映射
        keyword_mappings = {
            "project_overview": [
                "项目总览", "项目概况", "项目状态", "查看项目",
                "项目情况", "项目进展", "项目概览",
            ],
            "weekly_report": [
                "周报", "生成周报", "本周周报", "写周报",
                "汇报", "每周汇报", "工作周报",
            ],
            "wbs_generation": [
                "WBS", "wbs", "任务分解", "工作分解", "生成wbs",
                "分解任务", "任务拆分",
            ],
            "task_update": [
                "更新任务", "任务进度", "完成任务", "任务状态",
                "进度更新", "修改任务",
            ],
            "risk_alert": [
                "风险", "风险预警", "查看风险", "项目风险",
                "风险识别", "风险状态",
            ],
            "cost_monitor": [
                "成本", "成本监控", "预算", "支出", "花费",
                "费用", "成本情况", "预算情况",
            ],
            "policy_qa": [
                "制度", "规范", "流程", "规定", "管理办法",
                "管理制度", "操作规范", "制度问答",
            ],
            "project_query": [
                "项目人员", "项目成员", "人员配置", "项目进度",
                "里程碑", "交付情况",
            ],
            "meeting_minutes": [
                "会议纪要", "纪要", "会议记录", "生成纪要",
                "会议总结",
            ],
            "compliance_review": [
                "合规", "初审", "立项材料", "预立项", "审核材料",
                "材料审核", "合规检查",
            ],
            # 成本相关Skill关键词
            "cost_estimation": [
                "成本估算", "工作量评估", "项目估价", "费用估算",
                "估算成本", "评估成本", "工作量计算", "人月估算",
            ],
            "cost_monitoring": [
                "挣值分析", "EVM分析", "evm", "成本绩效", "SPI",
                "CPI", "挣值", "进度偏差", "成本偏差", "完工估算",
            ],
            "cost_accounting": [
                "成本核算", "结算", "成本报表", "核算报告",
                "核算成本", "项目结算", "成本结算", "利润核算",
            ],
        }

        # 检查关键词匹配
        for skill_name, keywords in keyword_mappings.items():
            if available_skills and skill_name not in available_skills:
                continue

            for keyword in keywords:
                if keyword.lower() in user_message.lower():
                    return skill_name

        return None


class IntentRouterV2:
    """
    增强版意图路由器.

    支持多轮对话状态感知、项目上下文绑定。
    """

    def __init__(self) -> None:
        """初始化增强版意图路由器."""
        self._base_router = IntentRouter()

    async def recognize_with_context(
        self,
        user_message: str,
        user_context: UserContext,
        conversation_history: List[Dict[str, str]],
        available_skills: Optional[List[str]] = None,
    ) -> IntentResult:
        """
        基于上下文识别意图.

        Args:
            user_message: 用户消息
            user_context: 用户上下文
            conversation_history: 对话历史
            available_skills: 可用Skill列表

        Returns:
            IntentResult: 意图识别结果
        """
        # 如果有项目上下文，优先在该项目的可用Skill范围内识别
        if user_context.current_project:
            skill_registry = get_skill_registry()
            available_manifests = await skill_registry.get_available_skills_for_user(
                user_context,
            )
            available_skills = [m.skill_name for m in available_manifests]

        # 尝试快速匹配
        quick_match_result = await self._base_router.quick_match(
            user_message,
            available_skills,
        )

        if quick_match_result and quick_match_result in (available_skills or []):
            manifest = self._base_router._skill_registry.get_manifest(
                quick_match_result,
            )
            return IntentResult(
                intent_type=IntentType.SKILL_EXECUTION,
                matched_skill=quick_match_result,
                skill_description=manifest.display_name,
                confidence=0.85,  # 关键词匹配置信度
                extracted_params=self._extract_params_from_message(
                    user_message,
                    manifest,
                ),
            )

        # 使用LLM识别
        request = IntentRecognitionRequest(
            user_message=user_message,
            user_id=user_context.user_id,
            chat_id=user_context.chat_id,
            chat_type=user_context.chat_type,
            project_id=user_context.current_project,
            conversation_history=conversation_history,
            available_skills=available_skills or [],
        )

        return await self._base_router.recognize(request)

    def _extract_params_from_message(
        self,
        message: str,
        manifest: SkillManifest,
    ) -> Dict[str, Any]:
        """
        从消息中提取参数.

        Args:
            message: 用户消息
            manifest: Skill Manifest

        Returns:
            Dict: 提取的参数
        """
        params: Dict[str, Any] = {}
        input_schema = manifest.input_schema

        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # 简化提取逻辑：根据参数名推断
        for param_name, param_schema in properties.items():
            param_type = param_schema.get("type", "string")
            description = param_schema.get("description", "")

            # TODO: 使用LLM进行更智能的参数提取
            # 这里仅做简单匹配

        return params


# 全局意图路由器实例
_intent_router: Optional[IntentRouter] = None
_intent_router_v2: Optional[IntentRouterV2] = None


def get_intent_router() -> IntentRouter:
    """获取意图路由器实例."""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router


def get_intent_router_v2() -> IntentRouterV2:
    """获取增强版意图路由器实例."""
    global _intent_router_v2
    if _intent_router_v2 is None:
        _intent_router_v2 = IntentRouterV2()
    return _intent_router_v2