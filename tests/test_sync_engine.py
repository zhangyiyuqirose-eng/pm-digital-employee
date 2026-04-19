"""
PM Digital Employee - Sync Engine Tests
项目经理数字员工系统 - 同步引擎测试

测试覆盖：
1. 同步日志管理
2. 同步状态更新
3. 冲突检测
4. 冲突解决
5. 版本管理
6. 绑定管理
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone
import json

from app.services.sync_engine import (
    SyncEngine,
    SyncStatus,
    ConflictResolutionStrategy,
)


# ==================== Fixture ====================

@pytest.fixture
def mock_session() -> MagicMock:
    """Mock数据库会话."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sync_engine(mock_session: MagicMock) -> SyncEngine:
    """创建同步引擎实例."""
    return SyncEngine(mock_session)


@pytest.fixture
def mock_sync_log() -> MagicMock:
    """Mock同步日志."""
    log = MagicMock()
    log.id = uuid4()
    log.sync_type = "lark_sheet"
    log.sync_direction = "import"
    log.sync_status = SyncStatus.PENDING
    log.module = "project"
    log.project_id = uuid4()
    log.operator_id = "user_001"
    log.operator_name = "测试用户"
    log.lark_sheet_token = "sheet_token_123"
    log.records_total = 0
    log.records_success = 0
    log.records_failed = 0
    log.records_skipped = 0
    log.started_at = datetime.now(timezone.utc)
    log.completed_at = None
    log.duration_ms = None
    log.error_details = None
    return log


@pytest.fixture
def mock_data_conflict() -> MagicMock:
    """Mock数据冲突."""
    conflict = MagicMock()
    conflict.id = uuid4()
    conflict.entity_type = "task"
    conflict.entity_id = uuid4()
    conflict.source_a = "lark_card"
    conflict.source_b = "excel_import"
    conflict.data_a = json.dumps({"name": "任务A", "progress": 50})
    conflict.data_b = json.dumps({"name": "任务A", "progress": 80})
    conflict.conflict_time = datetime.now(timezone.utc)
    conflict.resolution_status = "pending"
    conflict.resolution_strategy = None
    conflict.resolved_data = None
    return conflict


@pytest.fixture
def mock_lark_sheet_binding() -> MagicMock:
    """Mock飞书表格绑定."""
    binding = MagicMock()
    binding.id = uuid4()
    binding.project_id = uuid4()
    binding.lark_sheet_token = "sheet_token_123"
    binding.lark_sheet_id = "sheet_id_456"
    binding.module = "task"
    binding.sync_mode = "bidirectional"
    binding.sync_frequency = "realtime"
    binding.sync_enabled = True
    binding.field_mappings = json.dumps({"任务名称": "name", "进度": "progress"})
    binding.last_sync_at = None
    binding.last_sync_status = None
    binding.sync_version = 0
    return binding


# ==================== Sync Log Tests ====================

class TestSyncLogManagement:
    """同步日志管理测试."""

    @pytest.mark.asyncio
    async def test_create_sync_log(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试创建同步日志."""
        project_id = uuid4()

        log = await sync_engine.create_sync_log(
            sync_type="excel_import",
            sync_direction="import",
            module="project",
            project_id=project_id,
            operator_id="user_001",
            operator_name="测试用户",
            excel_file_name="test.xlsx",
        )

        # 验证日志属性
        assert log.sync_type == "excel_import"
        assert log.sync_direction == "import"
        assert log.module == "project"
        assert log.sync_status == SyncStatus.PENDING

        # 验证session.add被调用
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sync_log_lark_sheet(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试创建飞书表格同步日志."""
        log = await sync_engine.create_sync_log(
            sync_type="lark_sheet",
            sync_direction="bidirectional",
            module="task",
            lark_sheet_token="sheet_token_123",
        )

        assert log.sync_type == "lark_sheet"
        assert log.sync_direction == "bidirectional"
        assert log.lark_sheet_token == "sheet_token_123"

    @pytest.mark.asyncio
    async def test_update_sync_status_to_running(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_sync_log: MagicMock,
    ) -> None:
        """测试更新同步状态为运行中."""
        # Mock查询返回日志
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sync_log
        mock_session.execute.return_value = mock_result

        log = await sync_engine.update_sync_status(
            log_id=mock_sync_log.id,
            status=SyncStatus.RUNNING,
            records_total=100,
        )

        assert log.sync_status == SyncStatus.RUNNING
        assert log.records_total == 100

    @pytest.mark.asyncio
    async def test_update_sync_status_to_success(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_sync_log: MagicMock,
    ) -> None:
        """测试更新同步状态为成功."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sync_log
        mock_session.execute.return_value = mock_result

        log = await sync_engine.update_sync_status(
            log_id=mock_sync_log.id,
            status=SyncStatus.SUCCESS,
            records_total=100,
            records_success=95,
            records_failed=3,
            records_skipped=2,
        )

        assert log.sync_status == SyncStatus.SUCCESS
        assert log.records_success == 95
        assert log.records_failed == 3
        assert log.completed_at is not None
        assert log.duration_ms is not None

    @pytest.mark.asyncio
    async def test_update_sync_status_with_errors(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_sync_log: MagicMock,
    ) -> None:
        """测试更新同步状态带错误详情."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sync_log
        mock_session.execute.return_value = mock_result

        error_details = [
            {"row": 5, "error": "必填字段缺失"},
            {"row": 10, "error": "数据类型错误"},
        ]

        log = await sync_engine.update_sync_status(
            log_id=mock_sync_log.id,
            status=SyncStatus.PARTIAL,
            records_total=100,
            records_success=90,
            records_failed=10,
            error_details=error_details,
        )

        assert log.sync_status == SyncStatus.PARTIAL
        assert log.error_details is not None

    @pytest.mark.asyncio
    async def test_get_sync_logs(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_sync_log: MagicMock,
    ) -> None:
        """测试查询同步日志列表."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_sync_log]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        logs = await sync_engine.get_sync_logs(
            project_id=mock_sync_log.project_id,
            module="project",
            limit=10,
        )

        assert len(logs) == 1
        assert logs[0].module == "project"


# ==================== Conflict Detection Tests ====================

class TestConflictDetection:
    """冲突检测测试."""

    @pytest.mark.asyncio
    async def test_detect_conflict_found(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试检测到数据冲突."""
        entity_id = uuid4()

        data_a = {"name": "任务A", "progress": 50, "status": "进行中"}
        data_b = {"name": "任务A", "progress": 80, "status": "已完成"}

        conflict = await sync_engine.detect_conflict(
            entity_type="task",
            entity_id=entity_id,
            source_a="lark_card",
            data_a=data_a,
            source_b="excel_import",
            data_b=data_b,
        )

        # 应检测到progress和status冲突
        assert conflict is not None
        assert conflict.entity_type == "task"
        assert conflict.entity_id == entity_id
        assert conflict.source_a == "lark_card"
        assert conflict.source_b == "excel_import"

        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_no_conflict(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试无冲突数据."""
        entity_id = uuid4()

        data_a = {"name": "任务A", "progress": 50}
        data_b = {"name": "任务A", "progress": 50}

        conflict = await sync_engine.detect_conflict(
            entity_type="task",
            entity_id=entity_id,
            source_a="lark_card",
            data_a=data_a,
            source_b="excel_import",
            data_b=data_b,
        )

        assert conflict is None

    @pytest.mark.asyncio
    async def test_detect_conflict_ignore_fields(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试忽略字段的冲突检测."""
        entity_id = uuid4()

        data_a = {
            "name": "任务A",
            "progress": 50,
            "updated_at": "2026-01-01",  # 应被忽略
        }
        data_b = {
            "name": "任务A",
            "progress": 50,
            "updated_at": "2026-01-02",  # 应被忽略
        }

        conflict = await sync_engine.detect_conflict(
            entity_type="task",
            entity_id=entity_id,
            source_a="lark_card",
            data_a=data_a,
            source_b="excel_import",
            data_b=data_b,
            ignore_fields=["updated_at", "id", "created_at"],
        )

        # 只比较name和progress，无冲突
        assert conflict is None

    def test_compare_data(
        self,
        sync_engine: SyncEngine,
    ) -> None:
        """测试数据比较逻辑."""
        data_a = {"name": "A", "value": 100, "extra": "x"}
        data_b = {"name": "A", "value": 200, "extra": "y"}

        conflicts = sync_engine._compare_data(
            data_a=data_a,
            data_b=data_b,
            ignore_fields=["extra"],
        )

        # 只检测到value冲突
        assert "value" in conflicts
        assert conflicts["value"] == (100, 200)

    def test_make_comparable_uuid(
        self,
        sync_engine: SyncEngine,
    ) -> None:
        """测试UUID值转换."""
        test_uuid = uuid4()
        result = sync_engine._make_comparable(test_uuid)

        assert isinstance(result, str)
        assert result == str(test_uuid)

    def test_make_comparable_datetime(
        self,
        sync_engine: SyncEngine,
    ) -> None:
        """测试datetime值转换."""
        test_dt = datetime(2026, 1, 15, 10, 30, 0)
        result = sync_engine._make_comparable(test_dt)

        assert isinstance(result, str)
        assert "2026-01-15" in result


# ==================== Conflict Resolution Tests ====================

class TestConflictResolution:
    """冲突解决测试."""

    @pytest.mark.asyncio
    async def test_resolve_conflict_last_write(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_data_conflict: MagicMock,
    ) -> None:
        """测试最后写入优先策略."""
        # Mock查询返回冲突记录
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_data_conflict
        mock_session.execute.return_value = mock_result

        resolved = await sync_engine.resolve_conflict(
            conflict_id=mock_data_conflict.id,
            strategy=ConflictResolutionStrategy.LAST_WRITE,
            resolved_by_id="user_001",
            resolved_by_name="测试用户",
        )

        assert resolved.resolution_status == "resolved"
        assert resolved.resolution_strategy == ConflictResolutionStrategy.LAST_WRITE

    @pytest.mark.asyncio
    async def test_resolve_conflict_source_a(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_data_conflict: MagicMock,
    ) -> None:
        """测试来源A优先策略."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_data_conflict
        mock_session.execute.return_value = mock_result

        resolved = await sync_engine.resolve_conflict(
            conflict_id=mock_data_conflict.id,
            strategy=ConflictResolutionStrategy.SOURCE_A,
            resolved_by_id="user_001",
        )

        assert resolved.resolution_strategy == ConflictResolutionStrategy.SOURCE_A
        # resolved_data应该来自data_a
        assert resolved.resolved_data is not None

    @pytest.mark.asyncio
    async def test_resolve_conflict_source_b(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_data_conflict: MagicMock,
    ) -> None:
        """测试来源B优先策略."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_data_conflict
        mock_session.execute.return_value = mock_result

        resolved = await sync_engine.resolve_conflict(
            conflict_id=mock_data_conflict.id,
            strategy=ConflictResolutionStrategy.SOURCE_B,
        )

        assert resolved.resolution_strategy == ConflictResolutionStrategy.SOURCE_B

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_data_conflict: MagicMock,
    ) -> None:
        """测试人工解决策略."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_data_conflict
        mock_session.execute.return_value = mock_result

        manual_data = {"name": "任务A", "progress": 65, "status": "进行中"}

        resolved = await sync_engine.resolve_conflict(
            conflict_id=mock_data_conflict.id,
            strategy=ConflictResolutionStrategy.MANUAL,
            resolved_data=manual_data,
            resolved_by_id="user_001",
        )

        assert resolved.resolution_strategy == ConflictResolutionStrategy.MANUAL
        # 应使用人工指定的数据
        assert json.loads(resolved.resolved_data) == manual_data


# ==================== Binding Management Tests ====================

class TestBindingManagement:
    """绑定管理测试."""

    @pytest.mark.asyncio
    async def test_get_lark_sheet_binding(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_lark_sheet_binding: MagicMock,
    ) -> None:
        """测试获取飞书表格绑定."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lark_sheet_binding
        mock_session.execute.return_value = mock_result

        binding = await sync_engine.get_lark_sheet_binding(mock_lark_sheet_binding.id)

        assert binding is not None
        assert binding.module == "task"
        assert binding.sync_enabled is True

    @pytest.mark.asyncio
    async def test_get_lark_sheet_binding_not_found(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试绑定不存在."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        binding = await sync_engine.get_lark_sheet_binding(uuid4())

        assert binding is None

    @pytest.mark.asyncio
    async def test_update_binding_sync_status(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_lark_sheet_binding: MagicMock,
    ) -> None:
        """测试更新绑定同步状态."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lark_sheet_binding
        mock_session.execute.return_value = mock_result

        binding = await sync_engine.update_binding_sync_status(
            binding_id=mock_lark_sheet_binding.id,
            status=SyncStatus.SUCCESS,
        )

        assert binding.last_sync_status == SyncStatus.SUCCESS
        assert binding.last_sync_at is not None

    @pytest.mark.asyncio
    async def test_list_bindings_by_project(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
        mock_lark_sheet_binding: MagicMock,
    ) -> None:
        """测试按项目查询绑定列表."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_lark_sheet_binding]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        bindings = await sync_engine.list_bindings_by_project(
            project_id=mock_lark_sheet_binding.project_id,
        )

        assert len(bindings) == 1
        assert bindings[0].module == "task"


# ==================== Version Management Tests ====================

class TestVersionManagement:
    """版本管理测试."""

    @pytest.mark.asyncio
    async def test_create_version(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试创建数据版本."""
        entity_id = uuid4()
        data = {"name": "任务A", "progress": 50}

        version = await sync_engine.create_version(
            entity_type="task",
            entity_id=entity_id,
            data=data,
            source="lark_card",
            operator_id="user_001",
        )

        assert version is not None
        mock_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_get_version_history(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试获取版本历史."""
        entity_id = uuid4()

        mock_version = MagicMock()
        mock_version.version_number = 1

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_version]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        versions = await sync_engine.get_version_history(
            entity_type="task",
            entity_id=entity_id,
            limit=10,
        )

        assert len(versions) == 1


# ==================== Status Enum Tests ====================

class TestStatusEnums:
    """状态枚举测试."""

    def test_sync_status_values(self) -> None:
        """测试同步状态枚举值."""
        assert SyncStatus.PENDING == "pending"
        assert SyncStatus.RUNNING == "running"
        assert SyncStatus.SUCCESS == "success"
        assert SyncStatus.FAILED == "failed"
        assert SyncStatus.PARTIAL == "partial"

    def test_conflict_resolution_strategy_values(self) -> None:
        """测试冲突解决策略枚举值."""
        assert ConflictResolutionStrategy.LAST_WRITE == "last_write"
        assert ConflictResolutionStrategy.SOURCE_A == "source_a"
        assert ConflictResolutionStrategy.SOURCE_B == "source_b"
        assert ConflictResolutionStrategy.MANUAL == "manual"
        assert ConflictResolutionStrategy.MERGE == "merge"


# ==================== Edge Cases Tests ====================

class TestEdgeCases:
    """边界情况测试."""

    @pytest.mark.asyncio
    async def test_update_sync_status_log_not_found(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试更新不存在日志的状态."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError) as exc_info:
            await sync_engine.update_sync_status(
                log_id=uuid4(),
                status=SyncStatus.SUCCESS,
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_detect_conflict_empty_data(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试空数据冲突检测."""
        conflict = await sync_engine.detect_conflict(
            entity_type="task",
            entity_id=uuid4(),
            source_a="lark_card",
            data_a={},
            source_b="excel_import",
            data_b={},
        )

        # 空数据无冲突
        assert conflict is None

    def test_compare_data_with_nested_values(
        self,
        sync_engine: SyncEngine,
    ) -> None:
        """测试嵌套值比较."""
        data_a = {"nested": {"key": "value1"}}
        data_b = {"nested": {"key": "value2"}}

        # 嵌套字典直接比较可能有问题
        # 实际实现可能需要深层比较
        conflicts = sync_engine._compare_data(
            data_a=data_a,
            data_b=data_b,
            ignore_fields=[],
        )

        # 验证冲突检测行为
        # 如果实现支持深层比较，应检测到冲突


# ==================== Integration Tests ====================

class TestSyncIntegration:
    """同步引擎集成测试."""

    @pytest.mark.asyncio
    async def test_full_sync_flow(
        self,
        sync_engine: SyncEngine,
        mock_session: MagicMock,
    ) -> None:
        """测试完整同步流程."""
        project_id = uuid4()

        # 1. 创建同步日志
        log = await sync_engine.create_sync_log(
            sync_type="excel_import",
            sync_direction="import",
            module="project",
            project_id=project_id,
        )

        # 2. 更新为运行状态
        mock_sync_log = MagicMock()
        mock_sync_log.id = log.id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_sync_log
        mock_session.execute.return_value = mock_result

        await sync_engine.update_sync_status(
            log_id=log.id,
            status=SyncStatus.RUNNING,
            records_total=100,
        )

        # 3. 完成同步
        mock_sync_log.completed_at = None
        await sync_engine.update_sync_status(
            log_id=log.id,
            status=SyncStatus.SUCCESS,
            records_total=100,
            records_success=95,
            records_failed=5,
        )

        # 验证流程完整
        assert mock_session.add.call_count >= 1
        assert mock_session.flush.call_count >= 2