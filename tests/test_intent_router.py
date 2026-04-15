"""
PM Digital Employee - Intent Router Tests
Tests for intent recognition and routing.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestIntentRouterV2:
    """Tests for IntentRouterV2."""

    @pytest.mark.asyncio
    async def test_route_to_known_skill(self):
        """Should route to a known skill with high confidence."""
        from app.orchestrator.intent_router import IntentRouterV2

        router = IntentRouterV2()

        # Mock LLM to return a skill intent
        with patch.object(router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate_with_structured_output = AsyncMock(
                return_value={
                    "intent_type": "skill",
                    "skill_name": "project_overview",
                    "confidence": 0.95,
                    "params": {"project_name": "Alpha"},
                }
            )

            result = await router.route("Show me project overview for Alpha")

            assert result.intent_type == "skill"
            assert result.skill_name == "project_overview"
            assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_route_conversational(self):
        """Should route conversational messages."""
        from app.orchestrator.intent_router import IntentRouterV2

        router = IntentRouterV2()

        with patch.object(router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate_with_structured_output = AsyncMock(
                return_value={
                    "intent_type": "conversational",
                    "skill_name": "",
                    "confidence": 0.9,
                    "params": {},
                }
            )

            result = await router.route("Hello, how are you?")

            assert result.intent_type == "conversational"

    @pytest.mark.asyncio
    async def test_route_with_low_confidence(self):
        """Should flag low confidence results."""
        from app.orchestrator.intent_router import IntentRouterV2

        router = IntentRouterV2()

        with patch.object(router, "_llm_gateway") as mock_gateway:
            mock_gateway.generate_with_structured_output = AsyncMock(
                return_value={
                    "intent_type": "skill",
                    "skill_name": "unknown_skill",
                    "confidence": 0.3,
                    "params": {},
                }
            )

            result = await router.route("some ambiguous input")

            assert result.confidence < 0.5

    def test_create_intent_result(self):
        """Should create IntentResult from dict."""
        from app.orchestrator.schemas import IntentResult

        data = {
            "intent_type": "skill",
            "skill_name": "test_skill",
            "confidence": 0.85,
            "params": {"key": "value"},
        }

        result = IntentResult(**data)

        assert result.intent_type == "skill"
        assert result.skill_name == "test_skill"
        assert result.confidence == 0.85
        assert result.params == {"key": "value"}
