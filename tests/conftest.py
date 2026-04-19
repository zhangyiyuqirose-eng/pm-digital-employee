"""
PM Digital Employee - Pytest Fixtures
Shared test fixtures for the PM Digital Employee test suite.

修复版本，避免autouse fixture导致的导入问题。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest


# ==================== Async Event Loop ====================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== Mock Database ====================


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock SQLAlchemy async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# ==================== Mock Lark Components ====================


@pytest.fixture
def mock_lark_client() -> MagicMock:
    """Mock Lark API client."""
    client = MagicMock()
    client.app_id = "test_app_id"
    client.app_secret = "test_app_secret"
    client.api_domain = "https://open.feishu.cn"
    client._tenant_token = "test_token"
    client._token_expire_time = 9999999999.0
    client.get_tenant_token = AsyncMock(return_value="test_token")
    client.send_message = AsyncMock(return_value={"code": 0, "msg": "ok"})
    client.send_text_message = AsyncMock(return_value={"code": 0, "msg": "ok"})
    client.send_interactive_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    client.send_to_chat = AsyncMock(return_value={"code": 0, "msg": "ok"})
    client.get_user_info = AsyncMock(
        return_value={"code": 0, "data": {"user": {"name": "Test User"}}}
    )
    return client


@pytest.fixture
def mock_lark_service(mock_lark_client: MagicMock) -> MagicMock:
    """Mock Lark service."""
    service = MagicMock()
    service._client = mock_lark_client
    service.client = mock_lark_client
    service.send_text = AsyncMock(return_value={"code": 0, "msg": "ok"})
    service.send_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    service.send_card_to_chat = AsyncMock(return_value={"code": 0, "msg": "ok"})
    service.send_error_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    service.send_success_card = AsyncMock(return_value={"code": 0, "msg": "ok"})
    service.get_user_info = AsyncMock(
        return_value={"code": 0, "data": {"user": {"name": "Test User"}}}
    )
    service.get_user_name = AsyncMock(return_value="Test User")
    service.create_card = MagicMock()
    return service


# ==================== Mock LLM ====================


@pytest.fixture
def mock_llm_response() -> str:
    """Sample mock LLM response."""
    return "This is a test response from the LLM."


@pytest.fixture
def mock_llm_gateway(mock_llm_response: str) -> MagicMock:
    """Mock LLM gateway."""
    gateway = MagicMock()
    gateway.generate = AsyncMock(return_value=mock_llm_response)
    gateway.generate_with_structured_output = AsyncMock(
        return_value={"intent": "test", "confidence": 0.95}
    )
    return gateway


# ==================== Mock Orchestrator Components ====================


@pytest.fixture
def mock_intent_router() -> MagicMock:
    """Mock intent router."""
    router = MagicMock()
    result = MagicMock()
    result.skill_name = "test_skill"
    result.skill_display_name = "Test Skill"
    result.intent_type = "skill"
    result.confidence = 0.95
    result.params = {}
    result.requires_confirmation = False
    router.route = AsyncMock(return_value=result)
    router.recognize_with_context = AsyncMock(return_value=result)
    return router


@pytest.fixture
def mock_skill_registry() -> MagicMock:
    """Mock skill registry."""
    registry = MagicMock()
    result = MagicMock()
    result.success = True
    result.skill_name = "test_skill"
    result.presentation_type = "text"
    result.presentation_data = {"text": "Test result."}
    result.requires_confirmation = False
    result.is_async = False
    registry.execute_skill = AsyncMock(return_value=result)
    registry.get_skill_manifest = MagicMock(return_value=None)
    return registry


@pytest.fixture
def mock_dialog_state_machine() -> MagicMock:
    """Mock dialog state machine."""
    machine = MagicMock()
    session = MagicMock()
    session.state = "IDLE"
    session.user_id = "test_user"
    session.chat_id = "test_chat"
    machine.get_or_create_session = AsyncMock(return_value=session)
    machine.update_state = AsyncMock(return_value=session)
    return machine


@pytest.fixture
def mock_context_service() -> MagicMock:
    """Mock context service."""
    service = MagicMock()
    context = MagicMock()
    context.user_id = "test_user"
    context.user_name = "Test User"
    context.current_project = uuid4()
    context.user_role = None
    context.accessible_projects = [uuid4()]
    context.permissions = {"read": ["project"], "write": ["project"]}
    context.chat_id = "test_chat"
    context.chat_type = "p2p"
    service.build_user_context = AsyncMock(return_value=context)
    return service


# ==================== Conditional Global Mock Patching ====================


@pytest.fixture
def patch_global_services(
    mock_lark_service: MagicMock,
    mock_llm_gateway: MagicMock,
    mock_intent_router: MagicMock,
    mock_skill_registry: MagicMock,
    mock_dialog_state_machine: MagicMock,
    mock_context_service: MagicMock,
) -> Generator[None, None, None]:
    """
    Patch global service getters for tests that need them.

    Use this fixture explicitly in tests that require mocking global services.
    Not autouse to avoid import issues with utils tests.
    """
    import sys

    # Ensure modules are imported before patching
    patches = []

    try:
        from unittest.mock import patch as mock_patch

        # Only patch if module exists
        if "app.integrations.lark.service" in sys.modules:
            patches.append(mock_patch("app.integrations.lark.service.get_lark_service", return_value=mock_lark_service))

        if "app.ai.llm_gateway" in sys.modules:
            patches.append(mock_patch("app.ai.llm_gateway.get_llm_gateway", return_value=mock_llm_gateway))

        if "app.orchestrator.intent_router" in sys.modules:
            patches.append(mock_patch("app.orchestrator.intent_router.get_intent_router_v2", return_value=mock_intent_router))

        if "app.orchestrator.skill_registry" in sys.modules:
            patches.append(mock_patch("app.orchestrator.skill_registry.get_skill_registry", return_value=mock_skill_registry))

        if "app.orchestrator.dialog_state" in sys.modules:
            patches.append(mock_patch("app.orchestrator.dialog_state.get_dialog_state_machine", return_value=mock_dialog_state_machine))

        if "app.services.context_service" in sys.modules:
            patches.append(mock_patch("app.services.context_service.get_context_service", return_value=mock_context_service))

        # Start all patches
        for p in patches:
            p.start()

        yield

        # Stop all patches
        for p in patches:
            p.stop()

    except Exception:
        yield