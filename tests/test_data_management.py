"""
PM Digital Employee - Data Management API Tests
数据管理API全量测试
"""

import pytest
import uuid
import httpx
import asyncio

# 测试配置
BASE_URL = "http://localhost:28000"
API_PREFIX = "/api/v1/data"


@pytest.fixture(scope="module")
def test_project_data():
    """测试项目数据."""
    return {
        "name": f"测试项目-{uuid.uuid4().hex[:8]}",
        "code": f"TEST-{uuid.uuid4().hex[:6]}",
        "description": "自动化测试项目",
        "project_type": "研发项目",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
        "total_budget": 1000000.0,
    }


@pytest.fixture(scope="module")
def test_task_data():
    """测试任务数据."""
    return {
        "name": f"测试任务-{uuid.uuid4().hex[:8]}",
        "description": "自动化测试任务",
        "assignee_id": "ou_test_user",
        "start_date": "2026-04-01",
        "end_date": "2026-04-15",
        "priority": 1,
        "status": "未开始",
    }


@pytest.fixture(scope="module")
def test_risk_data():
    """测试风险数据."""
    return {
        "name": f"测试风险-{uuid.uuid4().hex[:8]}",
        "description": "自动化测试风险",
        "level": "中",
        "impact_scope": "进度影响",
        "mitigation_plan": "增加资源投入",
        "owner_id": "ou_test_user",
    }


@pytest.fixture(scope="module")
def test_cost_data():
    """测试成本数据."""
    return {
        "cost_type": "budget",
        "category": "人力成本",
        "amount": 50000.0,
        "description": "测试预算",
    }


@pytest.fixture(scope="module")
def test_milestone_data():
    """测试里程碑数据."""
    return {
        "name": f"测试里程碑-{uuid.uuid4().hex[:8]}",
        "planned_date": "2026-05-01",
        "status": "未完成",
    }


class TestDataManagementAPI:
    """数据管理API测试类."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_create_project(self, test_project_data):
        """测试创建项目."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects",
                json=test_project_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "project_id" in data["data"]
            return data["data"]["project_id"]

    @pytest.mark.asyncio
    async def test_create_task(self, test_task_data):
        """测试创建任务."""
        # 先创建项目
        async with httpx.AsyncClient() as client:
            project_resp = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects",
                json={"name": f"任务测试项目-{uuid.uuid4().hex[:8]}"},
            )
            project_data = project_resp.json()
            project_id = project_data["data"]["project_id"]

            # 创建任务
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects/{project_id}/tasks",
                json=test_task_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "task_id" in data["data"]

    @pytest.mark.asyncio
    async def test_create_risk(self, test_risk_data):
        """测试创建风险."""
        async with httpx.AsyncClient() as client:
            # 先创建项目
            project_resp = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects",
                json={"name": f"风险测试项目-{uuid.uuid4().hex[:8]}"},
            )
            project_data = project_resp.json()
            project_id = project_data["data"]["project_id"]

            # 创建风险
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects/{project_id}/risks",
                json=test_risk_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "risk_id" in data["data"]

    @pytest.mark.asyncio
    async def test_create_cost(self, test_cost_data):
        """测试创建成本."""
        async with httpx.AsyncClient() as client:
            # 先创建项目
            project_resp = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects",
                json={"name": f"成本测试项目-{uuid.uuid4().hex[:8]}"},
            )
            project_data = project_resp.json()
            project_id = project_data["data"]["project_id"]

            # 创建成本
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects/{project_id}/costs",
                json=test_cost_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "cost_id" in data["data"]

    @pytest.mark.asyncio
    async def test_create_milestone(self, test_milestone_data):
        """测试创建里程碑."""
        async with httpx.AsyncClient() as client:
            # 先创建项目
            project_resp = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects",
                json={"name": f"里程碑测试项目-{uuid.uuid4().hex[:8]}"},
            )
            project_data = project_resp.json()
            project_id = project_data["data"]["project_id"]

            # 创建里程碑
            response = await client.post(
                f"{BASE_URL}{API_PREFIX}/projects/{project_id}/milestones",
                json=test_milestone_data,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "milestone_id" in data["data"]

    @pytest.mark.asyncio
    async def test_skills_api(self):
        """测试Skills API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/v1/skills")
            assert response.status_code == 200
            data = response.json()
            assert len(data.get("skills", [])) == 13


class TestLarkCardForms:
    """飞书卡片表单测试."""

    def test_project_create_card(self):
        """测试项目创建卡片模板."""
        from app.integrations.lark.card_forms import build_project_create_card

        card = build_project_create_card()
        assert card is not None
        assert "header" in card

    def test_task_create_card(self):
        """测试任务录入卡片模板."""
        from app.integrations.lark.card_forms import build_task_create_card

        card = build_task_create_card("test-project-id", "测试项目")
        assert card is not None
        assert "header" in card

    def test_risk_create_card(self):
        """测试风险登记卡片模板."""
        from app.integrations.lark.card_forms import build_risk_create_card

        card = build_risk_create_card("test-project-id", "测试项目")
        assert card is not None
        assert "header" in card

    def test_cost_create_card(self):
        """测试成本录入卡片模板."""
        from app.integrations.lark.card_forms import build_cost_create_card

        card = build_cost_create_card("test-project-id", "测试项目")
        assert card is not None
        assert "header" in card

    def test_milestone_create_card(self):
        """测试里程碑卡片模板."""
        from app.integrations.lark.card_forms import build_milestone_create_card

        card = build_milestone_create_card("test-project-id", "测试项目")
        assert card is not None
        assert "header" in card

    def test_data_entry_menu_card(self):
        """测试数据录入菜单卡片模板."""
        from app.integrations.lark.card_forms import build_data_entry_menu_card

        card = build_data_entry_menu_card("test-project-id", "测试项目")
        assert card is not None
        assert "header" in card


class TestExceptionClasses:
    """异常类测试."""

    def test_task_not_found_error(self):
        """测试TaskNotFoundError异常."""
        from app.core.exceptions import TaskNotFoundError

        error = TaskNotFoundError(task_id="test-id")
        assert error.message == "任务不存在"
        assert error.details.get("task_id") == "test-id"

    def test_risk_not_found_error(self):
        """测试RiskNotFoundError异常."""
        from app.core.exceptions import RiskNotFoundError

        error = RiskNotFoundError(risk_id="test-id")
        assert error.message == "风险不存在"

    def test_milestone_not_found_error(self):
        """测试MilestoneNotFoundError异常."""
        from app.core.exceptions import MilestoneNotFoundError

        error = MilestoneNotFoundError(milestone_id="test-id")
        assert error.message == "里程碑不存在"

    def test_cost_not_found_error(self):
        """测试CostNotFoundError异常."""
        from app.core.exceptions import CostNotFoundError

        error = CostNotFoundError(cost_id="test-id")
        assert error.message == "成本不存在"