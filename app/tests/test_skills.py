"""
test skills for PM Digital Employee.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.skills.base import BaseSkill, SkillManifestBuilder
from app.skills.project_overview_skill import ProjectOverviewSkill
from app.skills.weekly_report_skill import WeeklyReportSkill
from app.orchestrator.schemas import SkillExecutionContext


class TestBaseSkill:
    """Test BaseSkill."""

    def test_skill_name(self):
        """Test skill name property."""
        skill = ProjectOverviewSkill()
        assert skill.skill_name == "project_overview"

    def test_skill_display_name(self):
        """Test skill display name property."""
        skill = ProjectOverviewSkill()
        assert skill.display_name == "项目总览"

    def test_get_manifest(self):
        """Test getting skill manifest."""
        skill = ProjectOverviewSkill()
        manifest = skill.get_manifest()

        assert manifest["skill_name"] == "project_overview"
        assert "input_schema" in manifest
        assert "output_schema" in manifest


class TestSkillManifestBuilder:
    """Test SkillManifestBuilder."""

    def test_build_manifest(self):
        """Test building manifest."""
        builder = SkillManifestBuilder(
            skill_name="test_skill",
            display_name="测试技能",
            description="测试技能描述",
        )

        manifest = builder.build()

        assert manifest["skill_name"] == "test_skill"
        assert manifest["display_name"] == "测试技能"

    def test_add_input_field(self):
        """Test adding input field."""
        builder = SkillManifestBuilder(
            skill_name="test_skill",
            display_name="测试",
            description="测试",
        )

        builder.add_input_field(
            name="project_id",
            type="string",
            description="项目ID",
            required=True,
        )

        manifest = builder.build()
        assert "project_id" in manifest["input_schema"]["properties"]
        assert "project_id" in manifest["input_schema"]["required"]

    def test_add_permission(self):
        """Test adding permission."""
        builder = SkillManifestBuilder(
            skill_name="test_skill",
            display_name="测试",
            description="测试",
        )

        builder.add_permission(resource="project", action="read")

        manifest = builder.build()
        assert len(manifest["required_permissions"]) == 1
        assert manifest["required_permissions"][0]["resource"] == "project"


class TestProjectOverviewSkill:
    """Test ProjectOverviewSkill."""

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test skill execution."""
        skill = ProjectOverviewSkill()

        context = SkillExecutionContext(
            user_id="test_user",
            project_id="test_project",
            session_id="test_session",
            input_data={},
        )

        # Mock project service
        with patch.object(skill, "_get_project_data", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "name": "测试项目",
                "status": "进行中",
                "progress": 50,
            }

            result = await skill.execute(context)

            assert result["name"] == "测试项目"
            assert result["progress"] == 50

    def test_validate_input(self):
        """Test input validation."""
        skill = ProjectOverviewSkill()

        # Valid input
        valid, errors = skill.validate_input({"project_id": "test_project"})
        assert valid is True

        # Missing project_id
        valid, errors = skill.validate_input({})
        assert valid is False
        assert "project_id" in errors


class TestWeeklyReportSkill:
    """Test WeeklyReportSkill."""

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test skill execution."""
        skill = WeeklyReportSkill()

        context = SkillExecutionContext(
            user_id="test_user",
            project_id="test_project",
            session_id="test_session",
            input_data={"week_start": "2026-03-01", "week_end": "2026-03-07"},
        )

        # Mock data collection
        with patch.object(skill, "_collect_project_data", new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = {
                "tasks_completed": ["任务1", "任务2"],
                "tasks_in_progress": ["任务3"],
                "risks": [],
            }

            # Mock report generation
            with patch.object(skill, "_generate_report_content", new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = "## 周报内容\n本周完成了..."

                result = await skill.execute(context)

                assert "report_content" in result

    def test_validate_input_with_week(self):
        """Test input validation with week dates."""
        skill = WeeklyReportSkill()

        valid, errors = skill.validate_input({
            "project_id": "test_project",
            "week_start": "2026-03-01",
            "week_end": "2026-03-07",
        })

        assert valid is True

    def test_validate_input_without_week(self):
        """Test input validation without week dates."""
        skill = WeeklyReportSkill()

        valid, errors = skill.validate_input({"project_id": "test_project"})

        # Should still be valid (will use current week)
        assert valid is True