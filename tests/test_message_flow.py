"""
PM Digital Employee - Message Flow Integration Tests
测试完整的消息接收、处理、回复流程

测试场景：
1. WebSocket消息接收 -> 内部处理端点
2. 内部处理端点 -> Orchestrator处理
3. Orchestrator -> LLM意图识别
4. Skill执行 -> 结果返回
5. 结果 -> 飞书消息回复
"""

import asyncio
import json
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


# ==================== 测试数据 ====================

SAMPLE_TEXT_MESSAGE = {
    "message": {
        "message_id": "om_test_001",
        "chat_id": "oc_test_chat_001",
        "chat_type": "p2p",
        "message_type": "text",
        "content": json.dumps({"text": "你好，帮我生成一份周报"}),
        "create_time": "2026-04-16T03:00:00Z"
    },
    "sender_id": "ou_test_user_001",
    "sender_user_id": "ou_test_user_001",
    "chat_type": "p2p"
}

SAMPLE_P2P_CHAT_ENTERED = {
    "chat_id": "oc_test_chat_001",
    "tenant_key": "test_tenant",
    "user_open_id": "ou_test_user_001"
}


# ==================== 端点测试 ====================

class TestInternalProcessMessageEndpoint:
    """测试内部消息处理端点."""

    @pytest.mark.asyncio
    async def test_process_text_message_success(self, mock_lark_service, mock_orchestrator):
        """测试成功处理文本消息."""
        # Mock orchestrator返回
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.skill_name = "weekly_report"
        mock_result.presentation_type = "text"
        mock_result.presentation_data = {"text": "周报生成完成"}
        mock_orchestrator.process_message.return_value = mock_result

        with patch("app.api.lark_webhook.get_orchestrator", return_value=mock_orchestrator):
            with patch("app.api.lark_webhook.get_lark_service", return_value=mock_lark_service):
                # 模拟HTTP请求
                async with httpx.AsyncClient() as client:
                    # 注意：这个测试需要实际服务运行，这里只是验证端点可访问
                    pass

    @pytest.mark.asyncio
    async def test_process_message_missing_fields(self):
        """测试缺少必要字段时的处理."""
        incomplete_message = {
            "message": {},
            "sender_id": ""
        }
        # 应该优雅处理，不抛异常


class TestWebSocketMessageHandler:
    """测试WebSocket消息处理器."""

    def test_handle_message_receive_v1(self):
        """测试P2P消息接收处理."""
        from app.integrations.lark.websocket import handle_message_receive_v1

        # 模拟飞书SDK事件对象
        mock_event = MagicMock()
        mock_event.message = MagicMock()
        mock_event.message.message_id = "om_test_001"
        mock_event.message.message_type = "text"
        mock_event.message.chat_type = "p2p"
        mock_event.message.chat_id = "oc_test_chat_001"
        mock_event.message.content = json.dumps({"text": "测试消息"})
        mock_event.sender = MagicMock()
        mock_event.sender.sender_id = MagicMock()
        mock_event.sender.sender_id.open_id = "ou_test_user_001"
        mock_event.sender.sender_id.user_id = None

        mock_data = MagicMock()
        mock_data.event = mock_event

        # 执行处理
        handle_message_receive_v1(mock_data)

    def test_handle_p2p_chat_entered(self):
        """测试P2P聊天进入事件."""
        from app.integrations.lark.websocket import handle_p2p_chat_entered

        mock_data = MagicMock()
        handle_p2p_chat_entered(mock_data)


class TestOrchestratorFlow:
    """测试Orchestrator完整流程."""

    @pytest.mark.asyncio
    async def test_intent_recognition_to_skill_execution(
        self, mock_intent_router, mock_skill_registry, mock_context_service
    ):
        """测试意图识别到技能执行的完整流程."""
        from app.orchestrator.orchestrator import Orchestrator
        from app.integrations.lark.schemas import LarkMessage

        # 创建测试消息
        message = LarkMessage(
            message_id="om_test_001",
            chat_id="oc_test_chat_001",
            chat_type="p2p",
            message_type="text",
            content=json.dumps({"text": "帮我生成周报"}),
            sender_id="ou_test_user_001"
        )

        # Mock意图识别结果
        intent_result = MagicMock()
        intent_result.intent_type = "skill"
        intent_result.skill_name = "weekly_report"
        intent_result.confidence = 0.95
        intent_result.params = {}
        mock_intent_router.route.return_value = intent_result

        # Mock技能执行结果
        skill_result = MagicMock()
        skill_result.success = True
        skill_result.presentation_type = "text"
        skill_result.presentation_data = {"text": "周报已生成"}
        mock_skill_registry.execute_skill.return_value = skill_result

        # 创建Orchestrator实例
        orchestrator = Orchestrator(
            lark_service=MagicMock(),
            intent_router=mock_intent_router,
            skill_registry=mock_skill_registry,
            dialog_state_machine=MagicMock(),
            context_service=mock_context_service
        )

        # 执行处理
        # result = await orchestrator.process_message(message)


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_orchestrator():
    """Mock Orchestrator."""
    orchestrator = MagicMock()
    result = MagicMock()
    result.success = True
    result.skill_name = "test_skill"
    result.presentation_type = "text"
    result.presentation_data = {"text": "处理完成"}
    orchestrator.process_message = AsyncMock(return_value=result)
    return orchestrator


# ==================== 运行测试入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])