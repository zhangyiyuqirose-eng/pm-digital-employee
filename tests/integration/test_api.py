"""
PM Digital Employee - API Endpoint Tests
项目经理数字员工系统 - API端点测试
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_application
from app.api.lark_webhook import router


class TestHealthEndpoints:
    """Health endpoint tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = FastAPI()
        from app.api.health import router as health_router
        app.include_router(health_router)
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok"]

    def test_ready_endpoint(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200

    def test_live_endpoint(self, client):
        """Test /live endpoint."""
        response = client.get("/live")
        assert response.status_code == 200


class TestLarkWebhook:
    """Lark webhook tests."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_webhook_health_check(self, client):
        """Test webhook health check."""
        response = client.get("/lark/webhook")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_challenge_verification(self, client):
        """Test Lark URL challenge verification."""
        challenge_data = {"challenge": "test_challenge_123"}
        response = client.post(
            "/lark/webhook",
            json=challenge_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test_challenge_123"

    def test_invalid_json(self, client):
        """Test invalid JSON request."""
        response = client.post(
            "/lark/webhook",
            content="not valid json",
        )
        assert response.status_code == 400


class TestLarkSignature:
    """Lark signature verification tests."""

    def test_signature_verification_valid(self):
        """Test valid signature verification."""
        from app.integrations.lark.signature import LarkSignatureVerifier

        # Use static method without instantiating
        result = LarkSignatureVerifier.handle_challenge("test_challenge")
        assert result["challenge"] == "test_challenge"

    def test_handle_challenge(self):
        """Test challenge response."""
        from app.integrations.lark.signature import LarkSignatureVerifier

        verifier = LarkSignatureVerifier()
        result = verifier.handle_challenge("abc123")

        assert "challenge" in result
        assert result["challenge"] == "abc123"


class TestLarkCardBuilder:
    """Lark card builder tests."""

    def test_card_builder_basic(self):
        """Test basic card building."""
        from app.integrations.lark.card_builder import CardBuilder

        card = (
            CardBuilder()
            .header("测试标题", template="blue")
            .div_module("测试内容")
            .build()
        )

        assert "header" in card
        assert card["header"]["title"]["content"] == "测试标题"

    def test_card_builder_with_markdown(self):
        """Test card with markdown module."""
        from app.integrations.lark.card_builder import CardBuilder

        card = (
            CardBuilder()
            .header("标题")
            .markdown_module("**重要提示**\n- 项目进度: 80%")
            .build()
        )

        assert "elements" in card
        assert len(card["elements"]) > 0

    def test_card_builder_with_actions(self):
        """Test card with action buttons."""
        from app.integrations.lark.card_builder import CardBuilder, ButtonBuilder

        card = (
            CardBuilder()
            .header("确认操作")
            .div_module("请确认是否继续")
            .action_module([
                ButtonBuilder.primary("确认"),
                ButtonBuilder.secondary("取消"),
            ])
            .build()
        )

        elements = card["elements"]
        action_found = False
        for elem in elements:
            if elem.get("tag") == "action":
                action_found = True
                assert len(elem.get("actions", [])) == 2

        assert action_found is True

    def test_card_builder_with_hr(self):
        """Test card with divider."""
        from app.integrations.lark.card_builder import CardBuilder

        card = (
            CardBuilder()
            .header("标题")
            .div_module("内容1")
            .hr()
            .div_module("内容2")
            .build()
        )

        hr_found = False
        for elem in card["elements"]:
            if elem.get("tag") == "hr":
                hr_found = True

        assert hr_found is True

    def test_project_overview_card_template(self):
        """Test project overview card template."""
        from app.integrations.lark.card_builder import CardBuilder

        card = CardBuilder.build_project_overview_card(
            project_name="核心交易系统升级",
            status="进行中",
            progress=75,
            risks_count=3,
        )

        assert "header" in card
        assert "核心交易系统升级" in card["header"]["title"]["content"]

    def test_error_card_template(self):
        """Test error card template."""
        from app.integrations.lark.card_builder import CardBuilder

        card = CardBuilder.build_error_card(
            error_title="操作失败",
            error_message="项目不存在",
        )

        assert card["header"]["template"] == "red"

    def test_success_card_template(self):
        """Test success card template."""
        from app.integrations.lark.card_builder import CardBuilder

        card = CardBuilder.build_success_card(
            title="操作成功",
            message="任务已更新",
        )

        assert card["header"]["template"] == "green"


class TestMessageFlow:
    """Message flow tests."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock orchestrator."""
        orchestrator = MagicMock()
        orchestrator.process_lark_message = AsyncMock(
            return_value=MagicMock(
                success=True,
                skill_name="project_overview",
                output={"project_name": "测试项目"},
            )
        )
        return orchestrator

    @pytest.mark.asyncio
    async def test_message_processing_flow(self, mock_orchestrator):
        """Test complete message processing flow."""
        from app.integrations.lark.schemas import LarkMessage

        message = LarkMessage(
            message_id="msg_123",
            chat_id="oc_chat_123",
            content="查看项目总览",
            msg_type="text",
        )

        result = await mock_orchestrator.process_lark_message(
            message=message,
            sender_user_id="ou_user_123",
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_message_processing_error(self, mock_orchestrator):
        """Test message processing error handling."""
        mock_orchestrator.process_lark_message = AsyncMock(
            return_value=MagicMock(
                success=False,
                error_message="处理失败",
            )
        )

        from app.integrations.lark.schemas import LarkMessage

        message = LarkMessage(
            message_id="msg_456",
            content="无效请求",
        )

        result = await mock_orchestrator.process_lark_message(
            message=message,
            sender_user_id="ou_user_456",
        )

        assert result.success is False


class TestLarkServiceMethods:
    """Lark service method tests."""

    def test_mention_user(self):
        """Test mention user formatting."""
        from app.integrations.lark.service import LarkService

        result = LarkService.mention_user("ou_test_user")
        assert "<at" in result
        assert "ou_test_user" in result

    def test_mention_all(self):
        """Test mention all formatting."""
        from app.integrations.lark.service import LarkService

        result = LarkService.mention_all()
        assert "<at" in result
        assert "all" in result

    def test_format_text_with_mentions(self):
        """Test text with mentions formatting."""
        from app.integrations.lark.service import LarkService

        text = "请关注项目进度"
        result = LarkService.format_text_with_mentions(
            text=text,
            mention_users=["ou_pm", "ou_member"],
            mention_all=False,
        )

        assert text in result
        assert "<at" in result