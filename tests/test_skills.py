"""
PM Digital Employee - Skills Unit Tests (Fixed v2)
项目经理数字员工系统 - Skill单元测试

基于实际schema定义编写正确的测试。
"""

import pytest
from uuid import uuid4

from app.skills.base import BaseSkill
from app.orchestrator.schemas import SkillExecutionResult, SkillExecutionContext, IntentType


class TestBaseSkill:
    """Test BaseSkill base class."""

    def test_skill_attributes(self):
        """Test skill attributes defined."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        skill = ProjectOverviewSkill()
        assert skill.skill_name == "project_overview"
        assert skill.display_name == "项目总览查询"
        assert skill.description != ""
        assert skill.version == "1.0.0"

    def test_get_manifest(self):
        """Test get_manifest returns valid manifest."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        manifest = ProjectOverviewSkill.get_manifest()
        assert manifest.skill_name == "project_overview"
        assert manifest.display_name == "项目总览查询"
        assert manifest.version == "1.0.0"

    def test_build_success_result(self):
        """Test build_success_result."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        skill = ProjectOverviewSkill()

        result = skill.build_success_result(
            output={"project_name": "测试项目"},
            presentation_type="text",
        )

        assert result.success is True
        assert result.output["project_name"] == "测试项目"

    def test_build_error_result(self):
        """Test build_error_result."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        skill = ProjectOverviewSkill()

        result = skill.build_error_result("项目不存在")

        assert result.success is False
        assert result.error_message == "项目不存在"

    def test_get_param_with_context(self):
        """Test get_param method with context."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        context = SkillExecutionContext(
            trace_id="trace_123",
            user_id="ou_test",
            chat_id="oc_test",
            skill_name="project_overview",
            params={"project_id": "test-123"},
        )
        skill = ProjectOverviewSkill(context=context)

        result = skill.get_param("project_id")
        assert result == "test-123"

        result = skill.get_param("missing", "default")
        assert result == "default"


class TestProjectOverviewSkill:
    """Test ProjectOverviewSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        skill = ProjectOverviewSkill()
        return skill

    def test_skill_name(self, skill):
        """Test skill name attribute."""
        assert skill.skill_name == "project_overview"

    def test_skill_display_name(self, skill):
        """Test skill display name."""
        assert skill.display_name == "项目总览查询"

    @pytest.mark.asyncio
    async def test_execute_no_project_id(self, skill):
        """Test execute without project_id."""
        result = await skill.execute()
        assert result.success is False
        assert "项目ID" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_mock_data(self):
        """Test execute returns mock data when no session."""
        from app.skills.project_overview_skill import ProjectOverviewSkill

        project_id = uuid4()
        context = SkillExecutionContext(
            trace_id="trace_456",
            user_id="ou_test",
            chat_id="oc_test",
            skill_name="project_overview",
            params={"project_id": str(project_id)},
        )
        skill = ProjectOverviewSkill(context=context)

        result = await skill.execute()

        # Returns mock data since no session
        assert result.success is True
        assert result.output["project_name"] == "示例项目"


class TestWeeklyReportSkill:
    """Test WeeklyReportSkill."""

    def test_skill_name_only(self):
        """Test skill name without initialization."""
        from app.skills.weekly_report_skill import WeeklyReportSkill

        # Test class attributes without instantiating
        assert WeeklyReportSkill.skill_name == "weekly_report"
        assert WeeklyReportSkill.display_name == "项目周报生成"

    def test_get_manifest(self):
        """Test manifest generation."""
        from app.skills.weekly_report_skill import WeeklyReportSkill

        manifest = WeeklyReportSkill.get_manifest()
        assert manifest.skill_name == "weekly_report"


class TestPolicyQASkill:
    """Test PolicyQASkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        from app.skills.policy_qa_skill import PolicyQASkill

        skill = PolicyQASkill()
        return skill

    def test_skill_name(self, skill):
        """Test skill name."""
        assert skill.skill_name == "policy_qa"

    def test_skill_display_name(self, skill):
        """Test skill display name."""
        assert skill.display_name == "项目制度规范答疑"


class TestRiskAlertSkill:
    """Test RiskAlertSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        from app.skills.risk_alert_skill import RiskAlertSkill

        skill = RiskAlertSkill()
        return skill

    def test_skill_name(self, skill):
        """Test skill name."""
        assert skill.skill_name == "risk_alert"

    def test_skill_display_name(self, skill):
        """Test skill display name."""
        assert skill.display_name == "风险识别与预警"


class TestCostMonitorSkill:
    """Test CostMonitorSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance."""
        from app.skills.cost_monitor_skill import CostMonitorSkill

        skill = CostMonitorSkill()
        return skill

    def test_skill_name(self, skill):
        """Test skill name."""
        assert skill.skill_name == "cost_monitor"

    def test_skill_display_name(self, skill):
        """Test skill display name."""
        assert skill.display_name == "成本监控"


class TestSkillExecutionResult:
    """Test SkillExecutionResult."""

    def test_success_result_creation(self):
        """Test creating success result."""
        result = SkillExecutionResult(
            success=True,
            skill_name="test_skill",
            output={"data": "value"},
            presentation_type="text",
        )

        assert result.success is True
        assert result.skill_name == "test_skill"
        assert result.output["data"] == "value"

    def test_error_result_creation(self):
        """Test creating error result."""
        result = SkillExecutionResult(
            success=False,
            skill_name="test_skill",
            error_message="执行失败",
        )

        assert result.success is False
        assert result.error_message == "执行失败"

    def test_model_dump(self):
        """Test model_dump method."""
        result = SkillExecutionResult(
            success=True,
            skill_name="test_skill",
            output={"key": "value"},
        )

        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["success"] is True


class TestSkillRegistration:
    """Test Skill registration."""

    def test_all_skills_registered(self):
        """Test all skills can be imported."""
        from app.skills import (
            ProjectOverviewSkill,
            WeeklyReportSkill,
            PolicyQASkill,
            RiskAlertSkill,
            CostMonitorSkill,
        )

        skills = [
            ProjectOverviewSkill,
            WeeklyReportSkill,
            PolicyQASkill,
            RiskAlertSkill,
            CostMonitorSkill,
        ]

        for skill_cls in skills:
            assert skill_cls.skill_name != ""
            assert skill_cls.display_name != ""