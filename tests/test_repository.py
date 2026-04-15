"""
PM Digital Employee - Repository Tests
Tests for ProjectScopedRepository and data access patterns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestProjectScopedRepository:
    """Tests for ProjectScopedRepository."""

    @pytest.mark.asyncio
    async def test_find_by_id_with_project_access(self, mock_session):
        """Should find entity when user has project access."""
        from app.repositories.base import ProjectScopedRepository

        project_id = uuid4()
        user_id = "test_user"

        # Mock a result
        mock_entity = MagicMock()
        mock_entity.id = uuid4()
        mock_entity.project_id = project_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_entity)
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProjectScopedRepository(session=mock_session)
        result = await repo.find_by_id(
            entity_id=mock_entity.id,
            project_id=project_id,
            user_id=user_id,
        )

        assert result is not None
        assert result.id == mock_entity.id

    @pytest.mark.asyncio
    async def test_find_by_id_no_project_access(self, mock_session):
        """Should raise error when user lacks project access."""
        from app.core.exceptions import ProjectAccessDeniedError
        from app.repositories.base import ProjectScopedRepository

        project_id = uuid4()
        user_id = "unauthorized_user"

        repo = ProjectScopedRepository(session=mock_session)

        with pytest.raises(ProjectAccessDeniedError):
            await repo.find_by_id(
                entity_id=uuid4(),
                project_id=project_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_find_all_with_project_filter(self, mock_session):
        """Should find all entities for a project."""
        from app.repositories.base import ProjectScopedRepository

        project_id = uuid4()
        user_id = "test_user"

        mock_entity1 = MagicMock()
        mock_entity1.id = uuid4()
        mock_entity2 = MagicMock()
        mock_entity2.id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars = MagicMock()
        mock_result.scalars.return_value.all = MagicMock(
            return_value=[mock_entity1, mock_entity2]
        )
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ProjectScopedRepository(session=mock_session)
        results = await repo.find_all_by_project(
            project_id=project_id,
            user_id=user_id,
        )

        assert len(results) == 2


class TestUserModel:
    """Tests for User domain model."""

    def test_user_display_name(self):
        """Should return name if available, else lark_user_id."""
        from app.domain.models.user import User

        user = User()
        user.name = "John Doe"
        user.lark_user_id = "ou_test123"

        assert user.display_name == "John Doe"

    def test_user_display_name_fallback(self):
        """Should fall back to lark_user_id if name is empty."""
        from app.domain.models.user import User

        user = User()
        user.name = ""
        user.lark_user_id = "ou_test123"

        assert user.display_name == "ou_test123"

    def test_user_repr(self):
        """Should include lark_user_id in repr."""
        from app.domain.models.user import User

        user = User()
        user.id = uuid4()
        user.name = "Test"
        user.lark_user_id = "ou_test123"

        repr_str = repr(user)
        assert "lark_user_id" in repr_str
        assert "ou_test123" in repr_str


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
