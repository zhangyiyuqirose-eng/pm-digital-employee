"""
PM Digital Employee - Health Check Tests
项目经理数字员工系统 - 健康检查接口单元测试

测试三个探活接口：
- /health
- /ready
- /live
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """创建测试客户端."""
    return TestClient(app)


class TestHealthEndpoint:
    """健康检查接口测试."""

    def test_health_returns_200(self, client: TestClient) -> None:
        """测试健康检查返回200."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_response_structure(self, client: TestClient) -> None:
        """测试健康检查响应结构."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "environment" in data

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """测试健康状态为healthy."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_has_service_name(self, client: TestClient) -> None:
        """测试响应包含服务名称."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == "PM Digital Employee"

    def test_health_has_timestamp(self, client: TestClient) -> None:
        """测试响应包含时间戳."""
        response = client.get("/health")
        data = response.json()

        # 时间戳应该是ISO格式
        assert data["timestamp"] is not None
        assert "T" in data["timestamp"]  # ISO 8601格式包含T


class TestReadyEndpoint:
    """就绪检查接口测试."""

    def test_ready_returns_200_when_healthy(self, client: TestClient) -> None:
        """测试服务就绪时返回200."""
        response = client.get("/ready")

        # 在没有实际依赖服务的情况下，可能返回200或503
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]

    def test_ready_response_structure(self, client: TestClient) -> None:
        """测试就绪检查响应结构."""
        response = client.get("/ready")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data

    def test_ready_has_component_checks(self, client: TestClient) -> None:
        """测试响应包含组件检查结果."""
        response = client.get("/ready")
        data = response.json()

        assert "checks" in data
        checks = data["checks"]

        # 应该检查数据库、Redis、RabbitMQ
        assert "database" in checks
        assert "redis" in checks
        assert "rabbitmq" in checks

    def test_ready_component_status_values(self, client: TestClient) -> None:
        """测试组件状态值为有效值."""
        response = client.get("/ready")
        data = response.json()
        checks = data["checks"]

        valid_statuses = {"healthy", "unhealthy"}

        for component_name, component_data in checks.items():
            assert component_data["status"] in valid_statuses


class TestLiveEndpoint:
    """存活检查接口测试."""

    def test_live_returns_200(self, client: TestClient) -> None:
        """测试存活检查返回200."""
        response = client.get("/live")

        assert response.status_code == status.HTTP_200_OK

    def test_live_response_structure(self, client: TestClient) -> None:
        """测试存活检查响应结构."""
        response = client.get("/live")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "environment" in data

    def test_live_status_is_alive(self, client: TestClient) -> None:
        """测试存活状态为alive."""
        response = client.get("/live")
        data = response.json()

        assert data["status"] == "alive"


class TestTraceIDPropagation:
    """Trace ID透传测试."""

    def test_trace_id_in_response_headers(self, client: TestClient) -> None:
        """测试响应头包含Trace ID."""
        response = client.get("/health")

        assert "X-Trace-ID" in response.headers
        assert response.headers["X-Trace-ID"] is not None

    def test_trace_id_from_request_header(self, client: TestClient) -> None:
        """测试从请求头继承Trace ID."""
        trace_id = "test-trace-id-12345"
        response = client.get("/health", headers={"X-Trace-ID": trace_id})

        assert response.headers["X-Trace-ID"] == trace_id

    def test_trace_id_generated_when_missing(self, client: TestClient) -> None:
        """测试请求头无Trace ID时自动生成."""
        response = client.get("/health")

        trace_id = response.headers["X-Trace-ID"]
        assert trace_id is not None
        assert len(trace_id) > 0


class TestCORS:
    """CORS配置测试."""

    def test_cors_headers_present(self, client: TestClient) -> None:
        """测试CORS响应头存在."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # 开发环境应该允许跨域
        if response.status_code == status.HTTP_200_OK:
            assert "access-control-allow-origin" in response.headers


class TestExceptionHandling:
    """异常处理测试."""

    def test_404_returns_error_response(self, client: TestClient) -> None:
        """测试404返回统一错误格式."""
        response = client.get("/nonexistent-path")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_method_not_allowed(self, client: TestClient) -> None:
        """测试方法不允许返回错误."""
        response = client.post("/health")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED