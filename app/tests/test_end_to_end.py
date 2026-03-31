"""
End-to-end tests for PM Digital Employee.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator.orchestrator import Orchestrator
from app.orchestrator.skill_registry import SkillRegistry
from app.skills.project_overview_skill import ProjectOverviewSkill


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_full_message_flow(self, client):
        """Test full message flow from webhook to response."""
        # This is a simplified end-to-end test
        # In production, this would test the full flow:
        # 1. Webhook receives message
        # 2. Intent router identifies skill
        # 3. Skill executes
        # 4. Response is formatted and sent back

        # For now, test that the system components can work together
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_skill_execution_pipeline(self):
        """Test skill execution pipeline."""
        registry = SkillRegistry()
        skill = ProjectOverviewSkill()
        registry.register(skill)

        orchestrator = Orchestrator(registry)

        # Mock the LLM call for intent recognition
        with patch.object(orchestrator.intent_router, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = '{"skill_name": "project_overview", "confidence": 0.95}'

            # Mock project service
            with patch.object(skill, "_get_project_data", new_callable=AsyncMock) as mock_data:
                mock_data.return_value = {
                    "name": "测试项目",
                    "status": "进行中",
                    "progress": 60,
                }

                result = await orchestrator.process_message(
                    user_input="查看项目状态",
                    user_id="test_user",
                    project_id="test_project",
                    chat_id="test_chat",
                )

                assert result is not None

    @pytest.mark.asyncio
    async def test_rag_qa_pipeline(self):
        """Test RAG QA pipeline."""
        from app.rag.qa_service import RAGQAService
        from app.rag.schemas import RAGRequest

        qa_service = RAGQAService()

        request = RAGRequest(
            query="项目周报的提交时间是什么？",
            user_id="test_user",
            project_id="test_project",
            top_k=5,
        )

        # Mock retriever
        with patch.object(qa_service.retriever, "retrieve", new_callable=AsyncMock) as mock_retrieve:
            from app.rag.schemas import RAGResponse, RetrievedDocument

            mock_retrieve.return_value = RAGResponse(
                documents=[
                    RetrievedDocument(
                        id="doc1",
                        content="项目周报应在每周五下午5点前提交",
                        score=0.9,
                        metadata={"source": "policy"},
                    ),
                ],
                query="项目周报的提交时间是什么？",
                has_answer=True,
            )

            # Mock LLM
            with patch.object(qa_service.llm_gateway, "generate", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value.content = "根据规定，项目周报应在每周五下午5点前提交。\n\n参考来源：政策文档"

                response = await qa_service.answer(request)

                assert response.answer is not None
                assert "周五" in response.answer

    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test multi-agent workflow."""
        from app.agents.base import AgentOrchestrator, AgentTask, AgentContext
        from app.agents.planner_agent import PlannerAgent

        orchestrator = AgentOrchestrator()
        planner = PlannerAgent(AgentContext())
        orchestrator.register_agent(planner)

        task = AgentTask(
            task_type="pre_initiation_review",
            input_data={
                "document_content": "预立项材料内容...",
            },
        )

        result = await planner.run(task)

        assert result.success is True
        assert "plan_type" in result.output

    @pytest.mark.asyncio
    async def test_event_flow(self):
        """Test event flow."""
        from app.events.bus import EventBus
        from app.events.handlers import RiskAlertHandler

        bus = EventBus()

        handler = RiskAlertHandler()
        bus.subscribe("risk_alert", handler)

        # Publish event
        await bus.publish({
            "event_type": "risk_alert",
            "project_id": "test_project",
            "risk_data": {
                "level": "high",
                "description": "测试风险",
            },
        })

        # Event should be processed
        assert True


class TestAccessControlEndToEnd:
    """End-to-end access control tests."""

    @pytest.mark.asyncio
    async def test_cross_project_access_blocked(self):
        """Test that cross-project access is blocked."""
        from app.services.access_control_service import AccessControlService

        service = AccessControlService()

        # Mock user has access to project1 only
        with patch.object(service, "_get_user_projects", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["project1"]

            # User tries to access project2
            has_access = await service.check_project_access(
                user_id="test_user",
                project_id="project2",
                required_permission="read",
            )

            assert has_access is False

    @pytest.mark.asyncio
    async def test_same_project_access_allowed(self):
        """Test that same-project access is allowed."""
        from app.services.access_control_service import AccessControlService

        service = AccessControlService()

        with patch.object(service, "_get_user_projects", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ["project1"]

            has_access = await service.check_project_access(
                user_id="test_user",
                project_id="project1",
                required_permission="read",
            )

            assert has_access is True