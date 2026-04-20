"""
PM Digital Employee - Dependency Injection Tests
Tests for dependency injection framework.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDependencyInjection:
    """Tests for dependency injection."""

    def test_get_lark_service_dep(self):
        """Should return Lark service."""
        from app.core.dependencies import get_lark_service_dep

        with patch('app.integrations.lark.service.get_lark_service') as mock:
            mock.return_value = MagicMock()
            result = get_lark_service_dep()
            assert result is not None

    def test_get_llm_gateway_dep(self):
        """Should return LLM gateway."""
        from app.core.dependencies import get_llm_gateway_dep

        with patch('app.ai.llm_gateway.get_llm_gateway') as mock:
            mock.return_value = MagicMock()
            result = get_llm_gateway_dep()
            assert result is not None

    def test_get_intent_router_dep(self):
        """Should return intent router."""
        from app.core.dependencies import get_intent_router_dep

        with patch('app.orchestrator.intent_router.get_intent_router_v2') as mock:
            mock.return_value = MagicMock()
            result = get_intent_router_dep()
            assert result is not None

    def test_get_skill_registry_dep(self):
        """Should return skill registry."""
        from app.core.dependencies import get_skill_registry_dep

        with patch('app.orchestrator.skill_registry.get_skill_registry') as mock:
            mock.return_value = MagicMock()
            result = get_skill_registry_dep()
            assert result is not None

    def test_get_encryptor_dep(self):
        """Should return encryptor."""
        from app.core.dependencies import get_encryptor_dep

        with patch('app.core.encryption.get_encryptor') as mock:
            mock.return_value = MagicMock()
            result = get_encryptor_dep()
            assert result is not None


class TestDependencyContainer:
    """Tests for DependencyContainer."""

    def test_container_initialization(self):
        """Should initialize container."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()
        assert container is not None
        assert len(container._dependencies) == 0
        assert len(container._instances) == 0

    def test_register_dependency(self):
        """Should register dependency."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()
        factory = MagicMock(return_value="test_instance")

        container.register("test", factory)
        assert "test" in container._dependencies

    def test_get_dependency(self):
        """Should get dependency instance."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()
        factory = MagicMock(return_value="test_instance")

        container.register("test", factory)
        result = container.get("test")

        assert result == "test_instance"
        factory.assert_called_once()

    def test_get_cached_dependency(self):
        """Should return cached instance."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()
        factory = MagicMock(return_value="test_instance")

        container.register("test", factory)
        result1 = container.get("test")
        result2 = container.get("test")

        assert result1 == result2
        factory.assert_called_once()  # Only called once due to caching

    def test_get_unregistered_dependency(self):
        """Should raise KeyError for unregistered dependency."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()

        with pytest.raises(KeyError):
            container.get("unregistered")

    def test_clear_instances(self):
        """Should clear cached instances."""
        from app.core.dependencies import DependencyContainer

        container = DependencyContainer()
        factory = MagicMock(return_value="test_instance")

        container.register("test", factory)
        container.get("test")  # Create instance
        container.clear()

        assert len(container._instances) == 0

    def test_get_container_singleton(self):
        """Should return same container instance."""
        from app.core.dependencies import get_container

        c1 = get_container()
        c2 = get_container()

        assert c1 is c2