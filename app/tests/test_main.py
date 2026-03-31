"""
PM Digital Employee - Tests
项目经理数字员工系统 - 测试文件
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """创建异步测试客户端."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestHealthEndpoints:
    """健康检查接口测试."""

    def test_health(self, client):
        """测试健康检查."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready(self, client):
        """测试就绪检查."""
        response = client.get("/ready")
        assert response.status_code == 200

    def test_live(self, client):
        """测试存活检查."""
        response = client.get("/live")
        assert response.status_code == 200


class TestLarkWebhook:
    """飞书Webhook测试."""

    def test_url_verification(self, client):
        """测试URL验证."""
        response = client.post(
            "/lark/webhook/url_verification",
            json={
                "challenge": "test_challenge",
                "token": "test_token",
                "type": "url_verification",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test_challenge"


class TestAccessControl:
    """权限控制测试."""

    def test_role_permission_matrix(self):
        """测试角色权限矩阵."""
        from app.services.access_control_service import ROLE_PERMISSION_MATRIX

        assert "project_manager" in ROLE_PERMISSION_MATRIX
        assert "pm" in ROLE_PERMISSION_MATRIX
        assert "tech_lead" in ROLE_PERMISSION_MATRIX
        assert "member" in ROLE_PERMISSION_MATRIX


class TestSkillRegistry:
    """Skill注册测试."""

    def test_skill_registration(self):
        """测试Skill注册."""
        from app.orchestrator.skill_registry import get_skill_registry

        registry = get_skill_registry()
        skills = registry.list_all_skills()

        assert len(skills) > 0


class TestInputValidator:
    """输入校验测试."""

    def test_sql_injection_detection(self):
        """测试SQL注入检测."""
        from app.security.input_validator import InputValidator

        assert not InputValidator.validate_sql_injection(
            "SELECT * FROM users",
        )

        assert InputValidator.validate_sql_injection(
            "正常输入内容",
        )

    def test_xss_detection(self):
        """测试XSS检测."""
        from app.security.input_validator import InputValidator

        assert not InputValidator.validate_xss(
            "<script>alert('xss')</script>",
        )

        assert InputValidator.validate_xss(
            "正常输入内容",
        )


class TestDataMasker:
    """数据脱敏测试."""

    def test_phone_masking(self):
        """测试手机号脱敏."""
        from app.security.input_validator import DataMasker

        masked = DataMasker.mask_phone("13812345678")
        assert masked == "138****5678"

    def test_id_card_masking(self):
        """测试身份证脱敏."""
        from app.security.input_validator import DataMasker

        masked = DataMasker.mask_id_card("110101199001011234")
        assert masked == "110101********1234"


class TestRAGChunker:
    """RAG切片测试."""

    def test_fixed_size_chunker(self):
        """测试固定大小切片."""
        from app.rag.chunker import FixedSizeChunker

        chunker = FixedSizeChunker()
        chunks = chunker.chunk(
            content="这是一段测试内容，用于测试固定大小切片功能。",
            chunk_size=10,
            chunk_overlap=2,
        )

        assert len(chunks) > 0

    def test_recursive_chunker(self):
        """测试递归切片."""
        from app.rag.chunker import RecursiveChunker

        chunker = RecursiveChunker()
        chunks = chunker.chunk(
            content="这是第一段。\n\n这是第二段。\n\n这是第三段。",
            chunk_size=20,
            chunk_overlap=5,
        )

        assert len(chunks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])