"""
PM Digital Employee - Lark Sheet Sync Service Tests
项目经理数字员工系统 - 飞书在线表格同步服务单元测试

测试覆盖：从飞书表格同步、从系统同步到飞书、字段映射、Webhook处理
"""

import pytest
import uuid
import json
from datetime import datetime, timezone, date
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.lark_sheet_sync_service import LarkSheetSyncService
from app.services.sync_engine import SyncStatus
from app.domain.enums import SyncMode


class TestLarkSheetSyncServiceInit:
    """服务初始化测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        return AsyncMock()

    def test_service_init(self, mock_session: MagicMock):
        """测试服务初始化."""
        service = LarkSheetSyncService(mock_session)

        assert service.session == mock_session
        assert service.sync_engine is not None
        assert service.validation_service is not None


class TestLarkSheetSyncServiceFromSheet:
    """从飞书表格同步测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_binding(self) -> MagicMock:
        """创建Mock绑定配置."""
        binding = MagicMock()
        binding.id = uuid.uuid4()
        binding.project_id = uuid.uuid4()
        binding.module = "task"
        binding.lark_sheet_token = "token_123"
        binding.lark_sheet_id = "sheet_456"
        binding.field_mappings = json.dumps({"任务名称": "name", "状态": "status"})
        binding.sync_enabled = True
        binding.sync_mode = "bidirectional"
        binding.data_range_start = "A1"
        binding.data_range_end = None
        return binding

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    @pytest.mark.asyncio
    async def test_sync_from_sheet_disabled_binding(self, service: LarkSheetSyncService, mock_binding: MagicMock):
        """测试禁用绑定的同步."""
        mock_binding.sync_enabled = False

        # Mock SyncEngine返回绑定
        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            result = await service.sync_from_sheet(mock_binding.id)

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_sync_from_sheet_binding_not_found(self, service: LarkSheetSyncService):
        """测试绑定不存在."""
        binding_id = uuid.uuid4()

        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                await service.sync_from_sheet(binding_id)

        assert "Binding not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_from_sheet_success(self, service: LarkSheetSyncService, mock_session: MagicMock, mock_binding: MagicMock):
        """测试成功同步."""
        # Mock绑定查询
        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            # Mock同步日志创建
            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            with patch.object(service.sync_engine, 'create_sync_log', return_value=mock_log):
                # Mock飞书表格数据读取
                sheet_data = [{"任务名称": "测试任务", "状态": "进行中"}]
                with patch.object(service, '_read_sheet_data', return_value=sheet_data):
                    # Mock状态更新
                    with patch.object(service.sync_engine, 'update_sync_status', return_value=None):
                        with patch.object(service.sync_engine, 'update_binding_sync_status', return_value=None):
                            # Mock导入数据
                            with patch.object(service, '_import_data_to_system', return_value={"imported": 1, "updated": 0}):
                                result = await service.sync_from_sheet(mock_binding.id)

        assert result["total"] == 1


class TestLarkSheetSyncServiceFieldMapping:
    """字段映射测试."""

    @pytest.fixture
    def service(self) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(AsyncMock())

    def test_field_mapping_basic(self, service: LarkSheetSyncService):
        """测试基本字段映射."""
        data = {"任务名称": "测试任务", "状态": "进行中"}
        mappings = {"任务名称": "name", "状态": "status"}

        result = service.field_mapping(data, mappings)

        assert result.get("name") == "测试任务"
        # 状态"进行中"会被转换为英文状态"in_progress"
        assert result.get("status") == "in_progress"

    def test_field_mapping_missing_column(self, service: LarkSheetSyncService):
        """测试缺失列的字段映射."""
        data = {"任务名称": "测试任务"}  # 缺失状态列
        mappings = {"任务名称": "name", "状态": "status"}

        result = service.field_mapping(data, mappings)

        assert result.get("name") == "测试任务"
        assert result.get("status") is None

    def test_field_mapping_preserves_sheet_row(self, service: LarkSheetSyncService):
        """测试保留飞书表格行号."""
        data = {"任务名称": "测试任务", "_lark_sheet_row": 5}
        mappings = {"任务名称": "name"}

        result = service.field_mapping(data, mappings)

        assert result.get("_lark_sheet_row") == 5

    def test_apply_field_mappings(self, service: LarkSheetSyncService):
        """测试批量应用字段映射."""
        sheet_data = [
            {"任务名称": "任务1", "状态": "进行中"},
            {"任务名称": "任务2", "状态": "已完成"},
        ]

        mock_binding = MagicMock()
        mock_binding.field_mappings = json.dumps({"任务名称": "name", "状态": "status"})

        result = service._apply_field_mappings(sheet_data, mock_binding)

        assert len(result) == 2
        assert result[0].get("name") == "任务1"
        assert result[1].get("name") == "任务2"

    def test_apply_field_mappings_invalid_json(self, service: LarkSheetSyncService):
        """测试无效JSON字段映射."""
        sheet_data = [{"任务名称": "任务1"}]

        mock_binding = MagicMock()
        mock_binding.field_mappings = "invalid_json"

        # 无效JSON时应返回原始数据
        result = service._apply_field_mappings(sheet_data, mock_binding)

        assert len(result) == 1


class TestLarkSheetSyncServiceValueConversion:
    """字段值转换测试."""

    @pytest.fixture
    def service(self) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(AsyncMock())

    def test_convert_date_field(self, service: LarkSheetSyncService):
        """测试日期字段转换."""
        result = service._convert_field_value("2026-04-19", "start_date")

        assert isinstance(result, date)
        assert result.year == 2026

    def test_convert_date_field_multiple_formats(self, service: LarkSheetSyncService):
        """测试多种日期格式转换."""
        # YYYY/MM/DD格式
        result1 = service._convert_field_value("2026/04/19", "start_date")
        assert isinstance(result1, date)

    def test_convert_numeric_field(self, service: LarkSheetSyncService):
        """测试数值字段转换."""
        result = service._convert_field_value("10000", "total_budget")

        assert isinstance(result, int)

    def test_convert_numeric_with_unit(self, service: LarkSheetSyncService):
        """测试带单位的数值转换."""
        result = service._convert_field_value("10000元", "total_budget")

        assert result == 10000

    def test_convert_progress_with_percent(self, service: LarkSheetSyncService):
        """测试带百分号的进度转换."""
        result = service._convert_field_value("50%", "progress")

        assert result == 50

    def test_convert_status_field_chinese(self, service: LarkSheetSyncService):
        """测试中文状态映射."""
        result = service._convert_field_value("进行中", "status")

        assert result == "in_progress"

    def test_convert_null_value(self, service: LarkSheetSyncService):
        """测试空值转换."""
        result = service._convert_field_value(None, "name")

        assert result is None

    def test_convert_empty_string(self, service: LarkSheetSyncService):
        """测试空字符串转换."""
        result = service._convert_field_value("", "name")

        assert result is None


class TestLarkSheetSyncServiceToSheet:
    """从系统同步到飞书表格测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_binding(self) -> MagicMock:
        """创建Mock绑定配置."""
        binding = MagicMock()
        binding.id = uuid.uuid4()
        binding.project_id = uuid.uuid4()
        binding.module = "task"
        binding.lark_sheet_token = "token_123"
        binding.lark_sheet_id = "sheet_456"
        binding.field_mappings = json.dumps({"name": "任务名称", "status": "状态"})
        binding.sync_enabled = True
        binding.sync_mode = "bidirectional"
        return binding

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    @pytest.mark.asyncio
    async def test_sync_to_sheet_disabled_binding(self, service: LarkSheetSyncService, mock_binding: MagicMock):
        """测试禁用绑定的同步."""
        mock_binding.sync_enabled = False

        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            result = await service.sync_to_sheet(mock_binding.id)

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_sync_to_sheet_binding_not_found(self, service: LarkSheetSyncService):
        """测试绑定不存在."""
        binding_id = uuid.uuid4()

        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                await service.sync_to_sheet(binding_id)

        assert "Binding not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_to_sheet_success(self, service: LarkSheetSyncService, mock_session: MagicMock, mock_binding: MagicMock):
        """测试成功同步到飞书."""
        # Mock绑定查询
        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            # Mock同步日志
            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            with patch.object(service.sync_engine, 'create_sync_log', return_value=mock_log):
                # Mock系统数据读取
                system_data = [{"name": "任务1", "status": "进行中"}]
                with patch.object(service, '_read_system_data', return_value=system_data):
                    # Mock写入飞书表格
                    with patch.object(service, '_write_sheet_data', return_value={"written": 1}):
                        with patch.object(service.sync_engine, 'update_sync_status', return_value=None):
                            with patch.object(service.sync_engine, 'update_binding_sync_status', return_value=None):
                                result = await service.sync_to_sheet(mock_binding.id)

        assert result["total"] == 1


class TestLarkSheetSyncServiceReverseMapping:
    """反向字段映射测试."""

    @pytest.fixture
    def service(self) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(AsyncMock())

    def test_apply_reverse_field_mappings(self, service: LarkSheetSyncService):
        """测试反向字段映射."""
        system_data = [{"name": "任务1", "status": "进行中"}]

        mock_binding = MagicMock()
        mock_binding.field_mappings = json.dumps({"任务名称": "name", "状态": "status"})

        result = service._apply_reverse_field_mappings(system_data, mock_binding)

        assert result[0].get("任务名称") == "任务1"
        assert result[0].get("状态") == "进行中"

    def test_format_sheet_value_date(self, service: LarkSheetSyncService):
        """测试日期值格式化."""
        test_date = date(2026, 4, 19)
        result = service._format_sheet_value(test_date, "日期")

        assert result == "2026-04-19"

    def test_format_sheet_value_decimal(self, service: LarkSheetSyncService):
        """测试Decimal值格式化."""
        test_decimal = Decimal("10000.50")
        result = service._format_sheet_value(test_decimal, "金额")

        assert result == 10000.50

    def test_format_sheet_value_uuid(self, service: LarkSheetSyncService):
        """测试UUID值格式化."""
        test_uuid = uuid.uuid4()
        result = service._format_sheet_value(test_uuid, "ID")

        assert isinstance(result, str)

    def test_format_sheet_value_none(self, service: LarkSheetSyncService):
        """测试None值格式化."""
        result = service._format_sheet_value(None, "字段")

        assert result == ""


class TestLarkSheetSyncServiceWebhook:
    """Webhook处理测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    @pytest.mark.asyncio
    async def test_handle_sheet_webhook_no_bindings(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试无活跃绑定的Webhook."""
        event_data = {
            "type": "sheet_data_change",
            "spreadsheet_token": "token_123",
            "sheet_id": "sheet_456",
        }

        # Mock查询返回空列表
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.handle_sheet_webhook(event_data)

        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_handle_sheet_webhook_with_bindings(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试有活跃绑定的Webhook."""
        event_data = {
            "type": "sheet_data_change",
            "spreadsheet_token": "token_123",
            "sheet_id": "sheet_456",
        }

        # Mock绑定列表
        mock_binding = MagicMock()
        mock_binding.id = uuid.uuid4()
        mock_binding.module = "task"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_binding]
        mock_session.execute.return_value = mock_result

        # Mock sync_from_sheet
        with patch.object(service, 'sync_from_sheet', return_value={"status": "success"}):
            result = await service.handle_sheet_webhook(event_data)

        assert result["status"] == "processed"
        assert result["sync_count"] == 1

    @pytest.mark.asyncio
    async def test_handle_sheet_webhook_sync_failure(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试Webhook同步失败."""
        event_data = {
            "type": "sheet_data_change",
            "spreadsheet_token": "token_123",
            "sheet_id": "sheet_456",
        }

        mock_binding = MagicMock()
        mock_binding.id = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_binding]
        mock_session.execute.return_value = mock_result

        # Mock sync_from_sheet失败
        with patch.object(service, 'sync_from_sheet', side_effect=Exception("同步失败")):
            result = await service.handle_sheet_webhook(event_data)

        assert result["status"] == "processed"
        assert len(result["results"]) == 1
        assert "error" in result["results"][0]


class TestLarkSheetSyncServiceImportData:
    """导入数据到系统测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    @pytest.mark.asyncio
    async def test_import_data_to_system_project(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试导入项目数据."""
        data_list = [{"name": "测试项目", "code": "PRJ001"}]
        project_id = uuid.uuid4()
        binding = MagicMock()
        binding.lark_sheet_token = "token_123"

        # Mock查找现有项目
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Mock创建项目
        with patch.object(service, '_create_project', return_value=MagicMock(id=uuid.uuid4())):
            with patch.object(service.sync_engine, 'record_version', return_value=None):
                result = await service._import_data_to_system(data_list, "project", project_id, binding)

        assert result["imported"] == 1

    @pytest.mark.asyncio
    async def test_import_data_to_system_task(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试导入任务数据."""
        data_list = [{"name": "测试任务", "status": "pending"}]
        project_id = uuid.uuid4()
        binding = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch.object(service, '_create_task', return_value=MagicMock()):
            result = await service._import_data_to_system(data_list, "task", project_id, binding)

        assert result["imported"] == 1


class TestLarkSheetSyncServiceFindExisting:
    """查找现有数据测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    @pytest.mark.asyncio
    async def test_find_existing_project_by_code(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试根据code查找项目."""
        mock_project = MagicMock()
        mock_project.code = "PRJ001"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_session.execute.return_value = mock_result

        result = await service._find_existing_project({"code": "PRJ001"})

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_existing_project_not_found(self, service: LarkSheetSyncService, mock_session: MagicMock):
        """测试查找不存在的项目."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service._find_existing_project({"name": "不存在项目"})

        assert result is None


class TestLarkSheetSyncServiceGetLarkClient:
    """飞书客户端获取测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    def test_get_lark_client_lazy_init(self, service: LarkSheetSyncService):
        """测试懒加载飞书客户端."""
        assert service._lark_client is None

        # Patch the actual import path used in _get_lark_client
        with patch('app.integrations.lark.service.get_lark_service') as mock_get_service:
            mock_service = MagicMock()
            mock_client = MagicMock()
            mock_service.client = mock_client
            mock_get_service.return_value = mock_service

            client = service._get_lark_client()

            assert client == mock_client
            assert service._lark_client == mock_client


class TestLarkSheetSyncServiceEdgeCases:
    """边界情况测试."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_session: MagicMock) -> LarkSheetSyncService:
        """创建服务实例."""
        return LarkSheetSyncService(mock_session)

    def test_convert_invalid_date(self, service: LarkSheetSyncService):
        """测试无效日期转换."""
        result = service._convert_field_value("invalid_date", "start_date")

        # 无法解析时返回原值
        assert result == "invalid_date"

    def test_convert_invalid_numeric(self, service: LarkSheetSyncService):
        """测试无效数值转换."""
        result = service._convert_field_value("abc", "total_budget")

        # 无法解析时返回原值
        assert result == "abc"

    @pytest.mark.asyncio
    async def test_sync_from_sheet_empty_data(self, service: LarkSheetSyncService):
        """测试空数据同步."""
        mock_binding = MagicMock()
        mock_binding.id = uuid.uuid4()
        mock_binding.sync_enabled = True
        mock_binding.field_mappings = json.dumps({"任务名称": "name", "状态": "status"})  # JSON字符串

        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            mock_log = MagicMock()
            mock_log.id = uuid.uuid4()
            with patch.object(service.sync_engine, 'create_sync_log', return_value=mock_log):
                with patch.object(service, '_read_sheet_data', return_value=[]):
                    with patch.object(service.sync_engine, 'update_sync_status', return_value=None):
                        with patch.object(service.sync_engine, 'update_binding_sync_status', return_value=None):
                            result = await service.sync_from_sheet(mock_binding.id)

        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_sync_to_sheet_empty_data(self, service: LarkSheetSyncService):
        """测试空数据同步到飞书."""
        mock_binding = MagicMock()
        mock_binding.id = uuid.uuid4()
        mock_binding.sync_enabled = True
        mock_binding.field_mappings = json.dumps({"任务名称": "name", "状态": "status"})  # JSON字符串

        with patch.object(service.sync_engine, 'get_lark_sheet_binding', return_value=mock_binding):
            mock_log = MagicMock()
            with patch.object(service.sync_engine, 'create_sync_log', return_value=mock_log):
                with patch.object(service, '_read_system_data', return_value=[]):
                    with patch.object(service, '_write_sheet_data', return_value={"written": 0}):
                        with patch.object(service.sync_engine, 'update_sync_status', return_value=None):
                            with patch.object(service.sync_engine, 'update_binding_sync_status', return_value=None):
                                result = await service.sync_to_sheet(mock_binding.id)

        assert result["total"] == 0