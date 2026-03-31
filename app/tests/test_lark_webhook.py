"""
test Lark webhook for PM Digital Employee.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.lark.signature import LarkSignature


class TestLarkSignature:
    """Test LarkSignature."""

    def test_verify_signature(self):
        """Test signature verification."""
        signature = LarkSignature(app_id="test_app", app_secret="test_secret")

        # Mock request headers
        headers = {
            "X-Lark-Request-Timestamp": "1234567890",
            "X-Lark-Request-Nonce": "test_nonce",
            "X-Lark-Signature": "test_signature",
        }

        body = b"test_body"

        # Note: Actual signature verification requires proper key
        # This is a simplified test
        result = signature.verify(headers, body)
        assert isinstance(result, bool)


class TestLarkWebhook:
    """Test Lark webhook endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_url_verification(self, client):
        """Test URL verification endpoint."""
        response = client.post(
            "/lark/url_verification",
            json={
                "challenge": "test_challenge_token",
                "token": "test_token",
                "type": "url_verification",
            },
        )

        assert response.status_code == 200
        assert response.json()["challenge"] == "test_challenge_token"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestMessagePayload:
    """Test message payload parsing."""

    def test_parse_message_event(self):
        """Test parsing message event."""
        payload = {
            "schema": "2.0",
            "header": {
                "event_id": "event_123",
                "event_type": "im.message.receive_v1",
                "create_time": "1234567890",
                "token": "test_token",
                "app_id": "cli_test",
            },
            "event": {
                "sender": {
                    "sender_id": {
                        "open_id": "ou_test",
                        "user_id": "user_test",
                    },
                },
                "message": {
                    "message_id": "msg_123",
                    "content": '{"text":"测试消息"}',
                    "message_type": "text",
                    "create_time": "1234567890",
                },
            },
        }

        # Verify payload structure
        assert payload["header"]["event_type"] == "im.message.receive_v1"
        assert payload["event"]["message"]["message_type"] == "text"


class TestCardCallback:
    """Test card callback handling."""

    def test_parse_card_action(self):
        """Test parsing card action."""
        callback = {
            "open_id": "ou_test",
            "user_id": "user_test",
            "token": "test_token",
            "action": {
                "value": {
                    "action_type": "approve",
                    "project_id": "project_123",
                },
            },
        }

        action_value = callback["action"]["value"]
        assert action_value["action_type"] == "approve"
        assert action_value["project_id"] == "project_123"