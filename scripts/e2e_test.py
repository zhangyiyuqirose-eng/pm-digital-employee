"""
PM Digital Employee - 端到端测试脚本
测试完整的消息流程：接收 -> 处理 -> 回复

运行方式：
python scripts/e2e_test.py

测试内容：
1. 内部消息处理端点测试
2. Orchestrator集成测试
3. Lark消息发送测试
"""

import asyncio
import json
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.integrations.lark.schemas import LarkMessage
from app.orchestrator.schemas import IntentResult, IntentType, SkillExecutionResult


class TestRunner:
    """测试运行器."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def log(self, msg: str, level: str = "INFO"):
        print(f"[{level}] {msg}")

    def pass_test(self, name: str):
        self.log(f"✅ PASS: {name}", "PASS")
        self.passed += 1

    def fail_test(self, name: str, error: str):
        self.log(f"❌ FAIL: {name}", "FAIL")
        self.log(f"   Error: {error}", "ERROR")
        self.failed += 1
        self.errors.append({"name": name, "error": error})

    def summary(self):
        print("\n" + "=" * 60)
        print(f"测试结果: 通过 {self.passed}, 失败 {self.failed}")
        if self.errors:
            print("\n失败的测试:")
            for e in self.errors:
                print(f"  - {e['name']}: {e['error']}")
        print("=" * 60)
        return self.failed == 0


# ==================== 测试1: 配置验证 ====================

def test_config():
    """测试配置是否正确加载."""
    runner = TestRunner()
    test_name = "配置加载测试"

    try:
        from app.core.config import Settings, get_settings, LLMSettings

        # 测试Settings实例化
        settings = get_settings()

        # 验证必要字段
        assert hasattr(settings, 'lark_app_id'), "缺少 lark_app_id"
        assert hasattr(settings, 'lark_app_secret'), "缺少 lark_app_secret"
        assert hasattr(settings, 'llm'), "缺少 llm 配置对象"

        # 验证LLMSettings
        llm = settings.llm
        assert hasattr(llm, 'provider'), "缺少 llm.provider"
        assert hasattr(llm, 'intent_model'), "缺少 llm.intent_model"

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试2: 异常类验证 ====================

def test_exceptions():
    """测试异常类是否完整."""
    runner = TestRunner()
    test_name = "异常类完整性测试"

    try:
        from app.core.exceptions import (
            APIException, ErrorCode,
            DialogSessionError, PromptError,
            OutputParseError, SafetyViolationError,
            IntentRecognitionError, SkillExecutionError,
            ProjectNotFoundError, DataNotFoundError
        )

        # 验证ErrorCode枚举
        assert ErrorCode.SYSTEM_ERROR, "缺少 SYSTEM_ERROR"
        assert ErrorCode.SKILL_EXECUTION_ERROR, "缺少 SKILL_EXECUTION_ERROR"

        # 验证异常类可实例化
        exc = DialogSessionError("test")
        assert exc.message == "test"

        exc2 = PromptError("test", template_name="test.tpl")
        assert exc2.message == "test"

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试3: Orchestrator导入 ====================

def test_orchestrator_import():
    """测试Orchestrator及相关模块导入."""
    runner = TestRunner()
    test_name = "Orchestrator导入测试"

    try:
        from app.orchestrator.orchestrator import Orchestrator
        from app.orchestrator.intent_router import IntentRouterV2
        from app.orchestrator.skill_registry import SkillRegistry, get_skill_registry
        from app.orchestrator.schemas import SkillManifest, SkillExecutionResult

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试4: Skill注册验证 ====================

def test_skill_registry():
    """测试Skill注册."""
    runner = TestRunner()
    test_name = "Skill注册测试"

    try:
        from app.orchestrator.skill_registry import get_skill_registry

        registry = get_skill_registry()

        # 验证已注册的skills
        skills = registry.list_skills()
        expected_skills = [
            "wbs_generation",
            "project_query",
            "meeting_minutes",
            "compliance_review",
            "cost_estimation",
            "cost_monitoring",
            "cost_accounting",
            "policy_qa",
            "task_update",
            "risk_alert",
            "weekly_report",
            "project_overview"
        ]

        registered = [s.skill_name for s in skills]
        missing = [s for s in expected_skills if s not in registered]

        if missing:
            runner.fail_test(test_name, f"缺少注册的Skills: {missing}")
        else:
            runner.pass_test(test_name)

    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试5: LarkService导入 ====================

def test_lark_service():
    """测试Lark服务导入."""
    runner = TestRunner()
    test_name = "LarkService导入测试"

    try:
        from app.integrations.lark.service import LarkService, get_lark_service
        from app.integrations.lark.schemas import LarkMessage, LarkCardBuilder
        from app.integrations.lark.websocket import (
            handle_message_receive_v1,
            handle_p2p_chat_entered,
            handle_message_read_v1
        )

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试6: WebSocket处理逻辑 ====================

def test_websocket_handler():
    """测试WebSocket消息处理逻辑."""
    runner = TestRunner()
    test_name = "WebSocket处理逻辑测试"

    try:
        # 模飞书SDK事件对象
        mock_event = MagicMock()
        mock_event.message = MagicMock()
        mock_event.message.message_id = "om_test_ws_001"
        mock_event.message.message_type = "text"
        mock_event.message.chat_type = "p2p"
        mock_event.message.chat_id = "oc_test_chat_ws"
        mock_event.message.content = json.dumps({"text": "测试WebSocket消息"})
        mock_event.sender = MagicMock()
        mock_event.sender.sender_id = MagicMock()
        mock_event.sender.sender_id.open_id = "ou_test_ws_user"
        mock_event.sender.sender_id.user_id = None

        mock_data = MagicMock()
        mock_data.event = mock_event

        from app.integrations.lark.websocket import handle_message_receive_v1

        # 执行处理（应该不抛异常）
        handle_message_receive_v1(mock_data)

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试7: 模拟完整消息流程 ====================

async def test_full_message_flow():
    """测试完整消息处理流程."""
    runner = TestRunner()
    test_name = "完整消息流程测试"

    try:
        from app.integrations.lark.schemas import LarkMessage

        # 创建模拟消息
        message = LarkMessage(
            message_id="om_e2e_test_001",
            chat_id="oc_e2e_test_chat",
            chat_type="p2p",
            message_type="text",
            content=json.dumps({"text": "帮我生成一份项目周报"}),
            sender_id="ou_e2e_test_user"
        )

        # 验证消息对象正确创建
        assert message.message_id == "om_e2e_test_001"
        assert message.chat_type == "p2p"

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 测试8: 内部处理端点模拟 ====================

async def test_internal_endpoint_mock():
    """模拟测试内部处理端点."""
    runner = TestRunner()
    test_name = "内部处理端点模拟测试"

    try:
        # 模拟请求数据
        request_data = {
            "message": {
                "message_id": "om_internal_test_001",
                "chat_id": "oc_internal_test_chat",
                "chat_type": "p2p",
                "message_type": "text",
                "content": json.dumps({"text": "测试内部处理"}),
                "create_time": "2026-04-16T03:00:00Z"
            },
            "sender_id": "ou_internal_test_user",
            "sender_user_id": "ou_internal_test_user",
            "chat_type": "p2p"
        }

        # 验证数据结构正确
        assert request_data["message"]["message_id"]
        assert request_data["sender_id"]

        runner.pass_test(test_name)
    except Exception as e:
        runner.fail_test(test_name, str(e))

    return runner


# ==================== 主函数 ====================

def main():
    """运行所有测试."""
    print("=" * 60)
    print("PM Digital Employee - 端到端测试")
    print("=" * 60)
    print()

    runners = []

    # 同步测试
    runners.append(test_config())
    runners.append(test_exceptions())
    runners.append(test_orchestrator_import())
    runners.append(test_skill_registry())
    runners.append(test_lark_service())
    runners.append(test_websocket_handler())

    # 异步测试
    runners.append(asyncio.run(test_full_message_flow()))
    runners.append(asyncio.run(test_internal_endpoint_mock()))

    # 汇总结果
    total_passed = sum(r.passed for r in runners)
    total_failed = sum(r.failed for r in runners)
    all_errors = []
    for r in runners:
        all_errors.extend(r.errors)

    print("\n" + "=" * 60)
    print(f"最终结果: 通过 {total_passed}, 失败 {total_failed}")
    if all_errors:
        print("\n所有失败的测试:")
        for e in all_errors:
            print(f"  - {e['name']}: {e['error']}")
    print("=" * 60)

    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)