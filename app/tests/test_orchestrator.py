"""
test orchestrator for PM Digital Employee.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.orchestrator.schemas import IntentResult, SkillExecutionContext
from app.orchestrator.skill_registry import SkillRegistry
from app.orchestrator.intent_router import IntentRouterV2
from app.orchestrator.orchestrator import Orchestrator
from app.skills.base import BaseSkill


class MockSkill(BaseSkill):
    """Mock skill for testing."""

    skill_name = "mock_skill"
    display_name = "Mock Skill"
    description = "A mock skill for testing"

    async def execute(self, context: SkillExecutionContext) -> dict:
        return {"result": "mock_result"}


class TestSkillRegistry:
    """Test SkillRegistry."""

    def test_register_skill(self):
        """Test skill registration."""
        registry = SkillRegistry()
        skill = MockSkill()
        registry.register(skill)

        assert registry.get_skill("mock_skill") == skill

    def test_get_all_skills(self):
        """Test getting all skills."""
        registry = SkillRegistry()
        skill = MockSkill()
        registry.register(skill)

        all_skills = registry.get_all_skills()
        assert len(all_skills) == 1
        assert all_skills[0].skill_name == "mock_skill"

    def test_skill_not_found(self):
        """Test getting non-existent skill."""
        registry = SkillRegistry()
        assert registry.get_skill("nonexistent") is None


class TestIntentRouterV2:
    """Test IntentRouterV2."""

    @pytest.mark.asyncio
    async def test_route_intent(self):
        """Test intent routing."""
        registry = SkillRegistry()
        skill = MockSkill()
        registry.register(skill)

        router = IntentRouterV2(registry)

        # Mock LLM response
        with patch.object(router, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"skill_name": "mock_skill", "confidence": 0.9}'

            result = await router.recognize_intent(
                user_input="测试输入",
                user_id="test_user",
                project_id="test_project",
            )

            assert result.skill_name == "mock_skill"
            assert result.confidence == 0.9


class TestOrchestrator:
    """Test Orchestrator."""

    @pytest.mark.asyncio
    async def test_execute_skill(self):
        """Test skill execution through orchestrator."""
        registry = SkillRegistry()
        skill = MockSkill()
        registry.register(skill)

        orchestrator = Orchestrator(registry)

        result = await orchestrator.execute_skill(
            skill_name="mock_skill",
            user_id="test_user",
            project_id="test_project",
            input_data={},
        )

        assert result["result"] == "mock_result"


class TestSkillExecutionContext:
    """Test SkillExecutionContext."""

    def test_create_context(self):
        """Test context creation."""
        context = SkillExecutionContext(
            user_id="test_user",
            project_id="test_project",
            session_id="test_session",
            input_data={"test": "data"},
        )

        assert context.user_id == "test_user"
        assert context.project_id == "test_project"
        assert context.input_data["test"] == "data"