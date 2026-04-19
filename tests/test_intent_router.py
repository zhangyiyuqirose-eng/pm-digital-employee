"""
PM Digital Employee - Intent Router Tests (Fixed)
Tests for intent recognition and routing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.schemas import IntentResult, IntentType


class TestIntentRouterV2:
    """Tests for IntentRouterV2."""

    @pytest.mark.asyncio
    async def test_route_to_known_skill(self):
        """Should route to a known skill with high confidence."""
        from app.orchestrator.intent_router import IntentRouterV2, IntentRouter
        from app.orchestrator.schemas import UserContext

        router = IntentRouterV2()

        # Mock base router's LLM gateway
        with patch.object(router._base_router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate = AsyncMock(
                return_value=MagicMock(
                    content='{"intent_type": "skill_execution", "matched_skill": "project_overview", "confidence": 0.95, "extracted_params": {"project_name": "Alpha"}}',
                    total_tokens=100,
                )
            )

            user_context = UserContext(user_id="ou_test", chat_id="oc_test")
            result = await router.recognize_with_context(
                user_message="Show me project overview for Alpha",
                user_context=user_context,
                conversation_history=[],
            )

            assert result.intent_type == IntentType.SKILL_EXECUTION
            assert result.matched_skill == "project_overview"
            assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_route_with_quick_match(self):
        """Should use quick match for keywords."""
        from app.orchestrator.intent_router import IntentRouter, IntentRouterV2
        from app.orchestrator.schemas import UserContext

        router = IntentRouter()
        user_context = UserContext(user_id="ou_test", chat_id="oc_test")

        # Quick match should work for "周报" keyword - use async method
        skill_name = await router.quick_match("帮我生成周报")

        # Should quick match to weekly_report
        assert skill_name == "weekly_report"

    @pytest.mark.asyncio
    async def test_quick_match_keywords(self):
        """Test quick_match keyword matching."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        # Test various keywords - quick_match is async
        assert await router.quick_match("帮我生成周报") == "weekly_report"
        assert await router.quick_match("查看项目总览") == "project_overview"
        assert await router.quick_match("有什么风险") == "risk_alert"
        assert await router.quick_match("成本监控") == "cost_monitor"
        assert await router.quick_match("更新任务进度") == "task_update"
        assert await router.quick_match("制度规范问答") == "policy_qa"

    @pytest.mark.asyncio
    async def test_quick_match_no_match(self):
        """Test quick_match returns None for no match."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        result = await router.quick_match("你好世界")
        assert result is None

    @pytest.mark.asyncio
    async def test_quick_match_with_available_skills(self):
        """Test quick_match with restricted skill list."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        # Only allow weekly_report and project_overview
        result = await router.quick_match(
            "成本监控",
            available_skills=["weekly_report", "project_overview"],
        )
        assert result is None  # cost_monitor not in available list

        result = await router.quick_match(
            "生成周报",
            available_skills=["weekly_report", "project_overview"],
        )
        assert result == "weekly_report"
        """Should route conversational messages."""
        from app.orchestrator.intent_router import IntentRouterV2, IntentRouter
        from app.orchestrator.schemas import UserContext

        router = IntentRouterV2()

        with patch.object(router._base_router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate = AsyncMock(
                return_value=MagicMock(
                    content='{"intent_type": "unknown", "matched_skill": null, "confidence": 0.0}',
                    total_tokens=50,
                )
            )

            user_context = UserContext(user_id="ou_test", chat_id="oc_test")
            result = await router.recognize_with_context(
                user_message="Hello, how are you?",
                user_context=user_context,
                conversation_history=[],
            )

            assert result.intent_type == IntentType.UNKNOWN

    @pytest.mark.asyncio
    async def test_route_with_low_confidence(self):
        """Should handle low confidence results."""
        from app.orchestrator.intent_router import IntentRouterV2, IntentRouter
        from app.orchestrator.schemas import UserContext

        router = IntentRouterV2()

        with patch.object(router._base_router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate = AsyncMock(
                return_value=MagicMock(
                    content='{"intent_type": "ambiguous", "matched_skill": null, "confidence": 0.3, "candidate_skills": [{"skill": "project_overview", "reason": "test"}]}',
                    total_tokens=80,
                )
            )

            user_context = UserContext(user_id="ou_test", chat_id="oc_test")
            result = await router.recognize_with_context(
                user_message="some ambiguous input",
                user_context=user_context,
                conversation_history=[],
            )

            assert result.confidence < 0.5

    def test_create_intent_result(self):
        """Should create IntentResult from dict."""
        data = {
            "intent_type": IntentType.SKILL_EXECUTION,
            "skill_name": "test_skill",
            "confidence": 0.85,
            "params": {"key": "value"},
        }

        result = IntentResult(
            intent_type=data["intent_type"],
            matched_skill=data["skill_name"],
            confidence=data["confidence"],
            extracted_params=data["params"],
        )

        assert result.intent_type == IntentType.SKILL_EXECUTION
        assert result.matched_skill == "test_skill"
        assert result.confidence == 0.85
        assert result.extracted_params == {"key": "value"}

    def test_intent_type_enum_values(self):
        """Test IntentType enum values."""
        assert IntentType.SKILL_EXECUTION.value == "skill_execution"
        assert IntentType.UNKNOWN.value == "unknown"
        assert IntentType.AMBIGUOUS.value == "ambiguous"
        assert IntentType.REJECTION.value == "rejection"


class TestIntentRouter:
    """Tests for base IntentRouter."""

    @pytest.mark.asyncio
    async def test_quick_match_keywords_basic(self):
        """Test quick_match keyword matching."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        # Test various keywords
        assert await router.quick_match("帮我生成周报") == "weekly_report"
        assert await router.quick_match("查看项目总览") == "project_overview"
        assert await router.quick_match("有什么风险") == "risk_alert"
        assert await router.quick_match("成本监控") == "cost_monitor"

    @pytest.mark.asyncio
    async def test_quick_match_no_match(self):
        """Test quick_match returns None for no match."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        result = await router.quick_match("你好世界")
        assert result is None

    @pytest.mark.asyncio
    async def test_quick_match_with_available_skills(self):
        """Test quick_match with restricted skill list."""
        from app.orchestrator.intent_router import IntentRouter

        router = IntentRouter()

        # Only allow weekly_report and project_overview
        result = await router.quick_match(
            "成本监控",
            available_skills=["weekly_report", "project_overview"],
        )
        assert result is None  # cost_monitor not in available list

        result = await router.quick_match(
            "生成周报",
            available_skills=["weekly_report", "project_overview"],
        )
        assert result == "weekly_report"