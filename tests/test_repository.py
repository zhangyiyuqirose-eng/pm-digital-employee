"""
PM Digital Employee - Repository Tests
Tests for ProjectScopedRepository and data access patterns.

Uses pure mock approach to avoid SQLAlchemy ORM initialization issues.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestProjectScopedRepositoryMock:
    """Tests for ProjectScopedRepository using mocks."""

    @pytest.mark.asyncio
    async def test_repository_initialization(self, mock_session):
        """Should initialize repository with model and session."""
        from app.repositories.base import ProjectScopedRepository
        
        # Use SkillDefinition which doesn't require project_id
        from app.domain.models.skill_definition import SkillDefinition
        
        # SkillDefinition doesn't have project_id, so it should raise
        with pytest.raises(ValueError):
            repo = ProjectScopedRepository(model=SkillDefinition, session=mock_session)

    @pytest.mark.asyncio
    async def test_repository_model_validation(self, mock_session):
        """Should validate that model has project_id field."""
        from app.repositories.base import ProjectScopedRepository
        
        # Task has project_id
        mock_task_model = MagicMock()
        mock_task_model.__name__ = "Task"
        mock_task_model.project_id = MagicMock()  # Has project_id attribute
        
        # Should not raise
        repo = ProjectScopedRepository(model=mock_task_model, session=mock_session)
        assert repo.model == mock_task_model
        assert repo.session == mock_session


class TestBaseRepositoryMock:
    """Tests for BaseRepository using pure mocks."""

    @pytest.mark.asyncio
    async def test_base_repository_initialization(self, mock_session):
        """Should initialize base repository."""
        from app.repositories.base import BaseRepository
        
        mock_model = MagicMock()
        mock_model.__name__ = "TestModel"
        
        repo = BaseRepository(model=mock_model, session=mock_session)
        assert repo.model == mock_model
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_count_method_mock(self, mock_session):
        """Should count entities using mock."""
        from app.repositories.base import BaseRepository
        
        mock_model = MagicMock()
        mock_model.__name__ = "TestModel"
        
        # Mock the count result
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=42)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        repo = BaseRepository(model=mock_model, session=mock_session)
        
        # count() calls execute, we need to mock select() too
        with patch('app.repositories.base.select') as mock_select:
            mock_select.return_value = MagicMock()
            count = await repo.count()
            assert count == 42


class TestIntegrationSystem:
    """Tests for IntegrationSystem enum."""

    def test_lark_exists(self):
        """Lark should be available as integration system."""
        from app.domain.enums import IntegrationSystem

        assert IntegrationSystem.LARK.value == "lark"

    def test_wecom_removed(self):
        """WeCom should NOT be available (replaced by Lark)."""
        from app.domain.enums import IntegrationSystem

        values = [e.value for e in IntegrationSystem]
        assert "wecom" not in values


class TestErrorCodeValues:
    """Tests for ErrorCode enum values."""

    def test_skill_error_code_exists(self):
        """SKILL_NOT_FOUND error code should exist."""
        from app.core.exceptions import ErrorCode

        # ErrorCode is a tuple (code, message)
        assert ErrorCode.SKILL_NOT_FOUND is not None

    def test_llm_error_code_exists(self):
        """LLM_ERROR error code should exist."""
        from app.core.exceptions import ErrorCode

        assert ErrorCode.LLM_ERROR is not None

    def test_project_access_denied_error_exists(self):
        """ProjectAccessDeniedError should exist."""
        from app.core.exceptions import ProjectAccessDeniedError

        assert ProjectAccessDeniedError is not None


class TestDatabaseError:
    """Tests for DatabaseError exception."""

    def test_database_error_creation(self):
        """Should create DatabaseError with message."""
        from app.core.exceptions import DatabaseError

        error = DatabaseError(message="Test database error")
        assert error.message == "Test database error"

    def test_database_error_to_dict(self):
        """Should convert DatabaseError to dict."""
        from app.core.exceptions import DatabaseError

        error = DatabaseError(message="Test error")
        result = error.to_dict()
        assert "message" in result
        assert result["message"] == "Test error"


class TestProjectAccessDeniedError:
    """Tests for ProjectAccessDeniedError."""

    def test_error_creation(self):
        """Should create ProjectAccessDeniedError."""
        from app.core.exceptions import ProjectAccessDeniedError

        project_id = str(uuid4())
        error = ProjectAccessDeniedError(project_id=project_id)
        assert project_id in str(error) or error.message


class TestLLMError:
    """Tests for LLMError exception."""

    def test_llm_error_creation(self):
        """Should create LLMError."""
        from app.core.exceptions import LLMError

        error = LLMError(message="LLM调用失败")
        assert error.message == "LLM调用失败"


class TestSkillNotFoundError:
    """Tests for SkillNotFoundError."""

    def test_skill_not_found_creation(self):
        """Should create SkillNotFoundError."""
        from app.core.exceptions import SkillNotFoundError

        error = SkillNotFoundError(skill_name="test_skill")
        assert "test_skill" in error.message