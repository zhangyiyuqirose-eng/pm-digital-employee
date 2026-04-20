"""
PM Digital Employee - Orchestrator Tests (Fixed v2)
项目经理数字员工系统 - 编排器测试

基于实际schema定义编写正确的测试。
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.orchestrator.schemas import (
    DialogState,
    UserContext,
    IntentResult,
    IntentType,
    SkillExecutionResult,
    SkillExecutionContext,
    SkillManifest,
)


class TestDialogState:
    """Test DialogState enum."""

    def test_states_exist(self):
        """Test all states exist."""
        assert hasattr(DialogState, "IDLE")
        assert hasattr(DialogState, "INTENT_RECOGNIZED")
        assert hasattr(DialogState, "PARAM_COLLECTING")
        assert hasattr(DialogState, "CONFIRMATION_PENDING")
        assert hasattr(DialogState, "EXECUTING")
        assert hasattr(DialogState, "COMPLETED")
        assert hasattr(DialogState, "FAILED")
        assert hasattr(DialogState, "CANCELLED")

    def test_state_values(self):
        """Test state values."""
        assert DialogState.IDLE.value == "idle"
        assert DialogState.PARAM_COLLECTING.value == "param_collecting"
        assert DialogState.CONFIRMATION_PENDING.value == "confirmation_pending"
        assert DialogState.EXECUTING.value == "executing"
        assert DialogState.COMPLETED.value == "completed"


class TestUserContext:
    """Test UserContext."""

    def test_creation_basic(self):
        """Test context creation with basic params."""
        context = UserContext(
            user_id="ou_test_user",
            chat_id="oc_test_chat",
        )

        assert context.user_id == "ou_test_user"
        assert context.chat_id == "oc_test_chat"

    def test_creation_with_project(self):
        """Test context creation with project."""
        project_id = uuid4()
        context = UserContext(
            user_id="ou_test_user",
            chat_id="oc_test_chat",
            current_project=project_id,
        )

        assert context.current_project == project_id

    def test_model_dump(self):
        """Test model_dump method (Pydantic v2)."""
        context = UserContext(
            user_id="ou_test",
            chat_id="oc_test",
        )

        data = context.model_dump()
        assert data["user_id"] == "ou_test"
        assert data["chat_id"] == "oc_test"


class TestIntentResult:
    """Test IntentResult."""

    def test_skill_execution_result(self):
        """Test skill execution intent result."""
        result = IntentResult(
            intent_type=IntentType.SKILL_EXECUTION,
            matched_skill="project_overview",
            confidence=0.95,
            extracted_params={"project_name": "测试项目"},
        )

        assert result.intent_type == IntentType.SKILL_EXECUTION
        assert result.matched_skill == "project_overview"
        assert result.confidence == 0.95

    def test_unknown_result(self):
        """Test unknown intent result."""
        result = IntentResult(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0,
        )

        assert result.intent_type == IntentType.UNKNOWN

    def test_rejection_result(self):
        """Test rejection intent result."""
        result = IntentResult(
            intent_type=IntentType.REJECTION,
            confidence=0.0,
            rejection_reason="安全防护触发",
        )

        assert result.intent_type == IntentType.REJECTION
        assert result.rejection_reason == "安全防护触发"


class TestSkillExecutionResult:
    """Test SkillExecutionResult."""

    def test_success_result(self):
        """Test success result."""
        result = SkillExecutionResult(
            success=True,
            skill_name="project_overview",
            output={"project_name": "测试项目"},
        )

        assert result.success is True
        assert result.skill_name == "project_overview"

    def test_error_result(self):
        """Test error result."""
        result = SkillExecutionResult(
            success=False,
            skill_name="test_skill",
            error_message="执行失败",
        )

        assert result.success is False
        assert result.error_message == "执行失败"

    def test_model_dump(self):
        """Test model_dump."""
        result = SkillExecutionResult(
            success=True,
            skill_name="test",
            output={"key": "value"},
        )

        data = result.model_dump()
        assert data["success"] is True
        assert data["skill_name"] == "test"

    def test_async_result(self):
        """Test async task result."""
        result = SkillExecutionResult(
            success=True,
            skill_name="weekly_report",
            is_async=True,
            async_task_id="task_123",
        )

        assert result.is_async is True
        assert result.async_task_id == "task_123"


class TestSkillExecutionContext:
    """Test SkillExecutionContext."""

    def test_context_creation_minimal(self):
        """Test minimal context creation."""
        context = SkillExecutionContext(
            trace_id="trace_123",
            user_id="ou_test",
            chat_id="oc_test",
            skill_name="project_overview",
        )

        assert context.trace_id == "trace_123"
        assert context.user_id == "ou_test"
        assert context.chat_id == "oc_test"
        assert context.skill_name == "project_overview"

    def test_context_creation_full(self):
        """Test full context creation."""
        project_id = uuid4()
        context = SkillExecutionContext(
            trace_id="trace_456",
            user_id="ou_test_user",
            chat_id="oc_test_chat",
            chat_type="group",
            project_id=project_id,
            user_role="project_manager",
            skill_name="weekly_report",
            params={"week": "2026-W16"},
        )

        assert context.chat_type == "group"
        assert context.project_id == project_id
        assert context.user_role == "project_manager"
        assert context.params["week"] == "2026-W16"


class TestSkillManifest:
    """Test SkillManifest."""

    def test_manifest_creation(self):
        """Test manifest creation."""
        manifest = SkillManifest(
            skill_name="project_overview",
            display_name="项目总览查询",
            description="查询项目整体状态",
            version="1.0.0",
        )

        assert manifest.skill_name == "project_overview"
        assert manifest.display_name == "项目总览查询"
        assert manifest.enabled_by_default is True

    def test_manifest_with_async(self):
        """Test manifest with async support."""
        manifest = SkillManifest(
            skill_name="weekly_report",
            display_name="周报生成",
            description="生成项目周报",
            supports_async=True,
        )

        assert manifest.supports_async is True


class TestIntentType:
    """Test IntentType enum."""

    def test_all_types_exist(self):
        """Test all intent types exist."""
        assert hasattr(IntentType, "SKILL_EXECUTION")
        assert hasattr(IntentType, "CLARIFICATION")
        assert hasattr(IntentType, "AMBIGUOUS")
        assert hasattr(IntentType, "UNKNOWN")
        assert hasattr(IntentType, "REJECTION")

    def test_type_values(self):
        """Test intent type values."""
        assert IntentType.SKILL_EXECUTION.value == "skill_execution"
        assert IntentType.UNKNOWN.value == "unknown"