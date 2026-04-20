"""
PM Digital Employee - Message Flow Tests (Fixed)
测试完整的消息接收、处理、回复流程
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestWebSocketMessageHandler:
    """测试WebSocket消息处理器."""

    def test_handle_message_receive_v1_import(self):
        """测试WebSocket处理函数导入."""
        try:
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

            mock_data = MagicMock()
            mock_data.event = mock_event

            # 执行处理
            handle_message_receive_v1(mock_data)

        except ImportError:
            pytest.skip("websocket module not implemented")

    def test_handle_p2p_chat_entered_import(self):
        """测试P2P聊天进入事件处理导入."""
        try:
            from app.integrations.lark.websocket import handle_p2p_chat_entered

            mock_data = MagicMock()
            handle_p2p_chat_entered(mock_data)

        except ImportError:
            pytest.skip("websocket module not implemented")


class TestOrchestratorFlow:
    """测试Orchestrator完整流程."""

    @pytest.mark.asyncio
    async def test_orchestrator_creation(self):
        """测试Orchestrator实例创建."""
        from app.orchestrator.orchestrator import Orchestrator

        # Orchestrator只接受session参数
        orchestrator = Orchestrator(session=None)
        assert orchestrator is not None

    @pytest.mark.asyncio
    async def test_orchestrator_process_message_mock(self):
        """测试Orchestrator消息处理（Mock）."""
        from app.orchestrator.orchestrator import Orchestrator
        from app.integrations.lark.schemas import LarkMessage

        orchestrator = Orchestrator(session=None)

        # Mock内部服务
        with patch.object(orchestrator, "_context_service") as mock_context:
            mock_context.build_user_context = AsyncMock(
                return_value=MagicMock(
                    user_id="ou_test",
                    chat_id="oc_test",
                    chat_type="p2p",
                    current_project=None,
                )
            )

            with patch.object(orchestrator._dialog_state_machine, "get_or_create_session") as mock_session:
                mock_session.return_value = MagicMock(
                    state="idle",
                    conversation_messages=[],
                    session_id="session_123",
                )

                with patch.object(orchestrator._intent_router, "recognize_with_context") as mock_intent:
                    mock_intent.return_value = MagicMock(
                        intent_type="unknown",
                        matched_skill=None,
                        confidence=0.0,
                    )

                    message = LarkMessage(
                        message_id="om_test_001",
                        chat_id="oc_test_chat_001",
                        chat_type="p2p",
                        message_type="text",
                        content=json.dumps({"text": "你好"}),
                        sender_id="ou_test_user_001"
                    )

                    result = await orchestrator.process_lark_message(
                        message=message,
                        sender_user_id="ou_test_user_001",
                    )

                    assert result is not None

    @pytest.mark.asyncio
    async def test_intent_recognition_to_skill_execution_mock(self):
        """测试意图识别到技能执行的完整流程（Mock）."""
        from app.orchestrator.orchestrator import Orchestrator
        from app.integrations.lark.schemas import LarkMessage
        from app.orchestrator.schemas import IntentResult, IntentType, SkillManifest

        orchestrator = Orchestrator(session=None)

        # Mock意图识别返回skill_execution
        intent_result = IntentResult(
            intent_type=IntentType.SKILL_EXECUTION,
            matched_skill="weekly_report",
            confidence=0.95,
            extracted_params={},
        )

        # Mock skill registry to return a manifest
        mock_manifest = SkillManifest(
            skill_name="weekly_report",
            display_name="项目周报生成",
            description="生成项目周报",
            version="1.0.0",
        )

        with patch.object(orchestrator._context_service, "build_user_context") as mock_context:
            mock_context.return_value = MagicMock(
                user_id="ou_test",
                chat_id="oc_test",
                chat_type="p2p",
                current_project=None,
            )

            with patch.object(orchestrator._dialog_state_machine, "get_or_create_session") as mock_session:
                mock_session.return_value = MagicMock(
                    state="idle",
                    conversation_messages=[],
                    session_id="session_123",
                    current_skill=None,
                    collected_params={},
                )

                with patch.object(orchestrator._dialog_state_machine, "transition") as mock_transition:
                    mock_transition.return_value = MagicMock(
                        state="param_collecting",
                        missing_params=["week"],
                    )

                    with patch.object(orchestrator._intent_router, "recognize_with_context") as mock_intent:
                        mock_intent.return_value = intent_result

                        with patch.object(orchestrator._skill_registry, "get_manifest") as mock_get_manifest:
                            mock_get_manifest.return_value = mock_manifest

                            message = LarkMessage(
                                message_id="om_test_001",
                                chat_id="oc_test_chat_001",
                                chat_type="p2p",
                                message_type="text",
                                content=json.dumps({"text": "帮我生成周报"}),
                                sender_id="ou_test_user_001"
                            )

                            result = await orchestrator.process_lark_message(
                                message=message,
                                sender_user_id="ou_test_user_001",
                            )

                            assert result is not None


class TestLarkMessageSchema:
    """测试Lark消息Schema."""

    def test_lark_message_creation(self):
        """测试LarkMessage创建."""
        from app.integrations.lark.schemas import LarkMessage

        message = LarkMessage(
            message_id="om_test_001",
            chat_id="oc_test_chat_001",
            chat_type="p2p",
            message_type="text",
            content=json.dumps({"text": "测试消息"}),
        )

        assert message.message_id == "om_test_001"
        assert message.chat_id == "oc_test_chat_001"
        assert message.message_type == "text"

    def test_lark_message_model_dump(self):
        """测试LarkMessage model_dump."""
        from app.integrations.lark.schemas import LarkMessage

        message = LarkMessage(
            message_id="om_test_001",
            content="test content",
        )

        data = message.model_dump()
        assert data["message_id"] == "om_test_001"


class TestParseConfirmation:
    """测试确认响应解析."""

    def test_parse_confirmation_positive(self):
        """测试正向确认关键词."""
        from app.orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator(session=None)

        assert orchestrator._parse_confirmation("确认") is True
        assert orchestrator._parse_confirmation("是") is True
        assert orchestrator._parse_confirmation("执行") is True
        assert orchestrator._parse_confirmation("好的") is True
        assert orchestrator._parse_confirmation("OK") is True
        assert orchestrator._parse_confirmation("可以") is True

    def test_parse_confirmation_negative(self):
        """测试负向确认关键词."""
        from app.orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator(session=None)

        assert orchestrator._parse_confirmation("取消") is False
        assert orchestrator._parse_confirmation("不") is False
        assert orchestrator._parse_confirmation("否") is False
        assert orchestrator._parse_confirmation("拒绝") is False
        assert orchestrator._parse_confirmation("算了") is False

    def test_parse_confirmation_default(self):
        """测试默认响应."""
        from app.orchestrator.orchestrator import Orchestrator

        orchestrator = Orchestrator(session=None)

        # 未知响应默认为不确认
        assert orchestrator._parse_confirmation("随便") is False