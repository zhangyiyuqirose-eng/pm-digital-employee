"""
PM Digital Employee - Lark Bitable Tests (Fixed)
飞书多维表格测试 - 修复API签名匹配
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestLarkBitableService:
    """Test LarkBitableService."""

    @pytest.fixture
    def mock_client(self):
        """Mock Lark client."""
        client = MagicMock()
        client.request = AsyncMock(return_value={"code": 0, "data": {}})
        return client

    def test_service_creation(self, mock_client):
        """Test service creation."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        assert service is not None
        assert service._client == mock_client

    @pytest.mark.asyncio
    async def test_create_app(self, mock_client):
        """Test create_app."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {"app": {"app_id": "app_123", "app_token": "token_abc"}}
        }

        result = await service.create_app(name="测试多维表格")

        # Returns the data dict
        assert "app" in result
        assert result["app"]["app_id"] == "app_123"

    @pytest.mark.asyncio
    async def test_create_table(self, mock_client):
        """Test create_table - uses fields parameter."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {"table": {"table_id": "tbl_123"}}
        }

        # create_table requires fields parameter
        result = await service.create_table(
            app_token="app_token_123",
            table_name="任务表",
            fields=[{"field_name": "任务名称", "type": 1}],
        )

        assert "table" in result
        assert result["table"]["table_id"] == "tbl_123"

    @pytest.mark.asyncio
    async def test_list_tables(self, mock_client):
        """Test list_tables."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {
                "items": [
                    {"table_id": "tbl_1", "name": "表1"},
                    {"table_id": "tbl_2", "name": "表2"},
                ]
            }
        }

        result = await service.list_tables(app_token="app_token_123")

        assert len(result) == 2
        assert result[0]["table_id"] == "tbl_1"

    @pytest.mark.asyncio
    async def test_add_records(self, mock_client):
        """Test add_records."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {"records": [{"record_id": "rec_123", "fields": {"任务名称": "测试任务"}}]}
        }

        records = [{"任务名称": "测试任务"}]
        result = await service.add_records(
            app_token="app_token_123",
            table_id="tbl_123",
            records=records,
        )

        assert len(result) == 1
        assert result[0]["record_id"] == "rec_123"

    @pytest.mark.asyncio
    async def test_search_records(self, mock_client):
        """Test search_records - returns dict with records."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {
                "records": [
                    {"record_id": "rec_1", "fields": {"状态": "完成"}},
                ],
                "has_more": False,
            }
        }

        # search_records returns a dict, not a list
        result = await service.search_records(
            app_token="app_token_123",
            table_id="tbl_123",
        )

        assert "records" in result
        assert len(result["records"]) == 1

    @pytest.mark.asyncio
    async def test_update_records(self, mock_client):
        """Test update_records."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {"records": [{"record_id": "rec_123"}]}
        }

        result = await service.update_records(
            app_token="app_token_123",
            table_id="tbl_123",
            records=[
                {"record_id": "rec_123", "fields": {"状态": "进行中"}}
            ]
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_records(self, mock_client):
        """Test delete_records."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {"code": 0}

        result = await service.delete_records(
            app_token="app_token_123",
            table_id="tbl_123",
            record_ids=["rec_123"],
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_record(self, mock_client):
        """Test get_record."""
        from app.integrations.lark.bitable import LarkBitableService

        service = LarkBitableService(client=mock_client)
        mock_client.request.return_value = {
            "code": 0,
            "data": {"record": {"record_id": "rec_123", "fields": {"name": "test"}}}
        }

        result = await service.get_record(
            app_token="app_token_123",
            table_id="tbl_123",
            record_id="rec_123",
        )

        assert result["record_id"] == "rec_123"


class TestProjectWorkspace:
    """Test project workspace creation."""

    @pytest.mark.asyncio
    async def test_create_project_workspace(self):
        """Test create_project_workspace."""
        from app.integrations.lark.bitable import LarkBitableService

        mock_client = MagicMock()
        mock_client.request = AsyncMock(side_effect=[
            # create_app
            {"code": 0, "data": {"app": {"app_id": "app_123", "app_token": "app_token_abc"}}},
            # create_table (任务)
            {"code": 0, "data": {"table": {"table_id": "tbl_tasks"}}},
            # create_table (风险)
            {"code": 0, "data": {"table": {"table_id": "tbl_risks"}}},
            # create_table (里程碑)
            {"code": 0, "data": {"table": {"table_id": "tbl_milestones"}}},
            # create_table (成本)
            {"code": 0, "data": {"table": {"table_id": "tbl_costs"}}},
        ])

        service = LarkBitableService(client=mock_client)

        result = await service.create_project_workspace(
            project_id=uuid4(),
            project_name="测试项目",
        )

        assert "app_token" in result
        assert "tables" in result
        assert len(result["tables"]) >= 2


class TestSyncOperations:
    """Test sync operations."""

    @pytest.mark.asyncio
    async def test_sync_project_data_to_bitable_no_session(self):
        """Test sync_project_data_to_bitable without session."""
        from app.integrations.lark.bitable import LarkBitableService

        mock_client = MagicMock()
        service = LarkBitableService(client=mock_client)

        # Without session, returns mock result
        result = await service.sync_project_data_to_bitable(
            project_id=uuid4(),
            app_token="app_123",
            table_ids={"任务表": "tbl_tasks"},
            session=None,
        )

        assert "tasks" in result
        assert result["tasks"] == 0  # No session means no data to sync