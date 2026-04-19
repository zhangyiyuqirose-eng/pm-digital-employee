"""
PM Digital Employee - Sync Engine Tests
项目经理数字员工系统 - 数据同步引擎单元测试

测试覆盖：同步日志管理、冲突检测与解决、版本记录管理、绑定配置管理
"""

import pytest
import uuid
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.sync_engine import SyncEngine, SyncStatus, ConflictResolutionStrategy


class TestSyncStatus:
    """SyncStatus常量测试."""

    def test_sync_status_values(self):
        """测试同步状态常量值."""
        assert SyncStatus.PENDING == "pending"
        assert SyncStatus.RUNNING == "running"
        assert SyncStatus.SUCCESS == "success"
        assert SyncStatus.FAILED == "failed"
        assert SyncStatus.PARTIAL == "partial"


class TestConflictResolutionStrategy:
    """冲突解决策略常量测试."""

    def test_strategy_values(self):
        """测试策略常量值."""
        assert ConflictResolutionStrategy.LAST_WRITE == "last_write"
        assert ConflictResolutionStrategy.SOURCE_A == "source_a"
        assert ConflictResolutionStrategy.SOURCE_B == "source_b"
        assert ConflictResolutionStrategy.MANUAL == "manual"
        assert ConflictResolutionStrategy.MERGE == "merge"


class TestSyncEngine:
    """SyncEngine测试类."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """创建Mock数据库会话."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def engine(self, mock_session: MagicMock) -> SyncEngine:
        """创建SyncEngine实例."""
        return SyncEngine(mock_session)

    # ==================== 同步日志测试 ====================

    @pytest.mark.asyncio
    async def test_create_sync_log(self, engine: SyncEngine, mock_session: MagicMock):
        """测试创建同步日志."""
        # 模拟返回的日志对象
        mock_log = MagicMock()
        mock_log.id = uuid.uuid4()
        mock_log.sync_type = "lark_sheet"
        mock_log.sync_direction = "import"

        mock_session.refresh.return_value = None

        result = await engine.create_sync_log(
            sync_type="lark_sheet",
            sync_direction="import",
            module="task",
            project_id=uuid.uuid4(),
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_create_sync_log_with_operator(self, engine: SyncEngine, mock_session: MagicMock):
        """测试创建同步日志带操作人信息."""
        await engine.create_sync_log(
            sync_type="lark_sheet",
            sync_direction="export",
            module="task",
            project_id=uuid.uuid4(),
            operator_id="user_123",
            operator_name="张三",
        )

        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_update_sync_status_success(self, engine: SyncEngine, mock_session: MagicMock):
        """测试更新同步状态为成功."""
        log_id = uuid.uuid4()

        # 模拟查询返回
        mock_result = MagicMock()
        mock_log = MagicMock()
        mock_log.id = log_id
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_session.execute.return_value = mock_result

        result = await engine.update_sync_status(
            log_id,
            SyncStatus.SUCCESS,
            records_total=10,
            records_success=10,
        )

        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_update_sync_status_with_errors(self, engine: SyncEngine, mock_session: MagicMock):
        """测试更新同步状态带错误详情."""
        log_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_log = MagicMock()
        mock_log.id = log_id
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_session.execute.return_value = mock_result

        errors = [{"row": 1, "error": "数据格式错误"}]
        result = await engine.update_sync_status(
            log_id,
            SyncStatus.PARTIAL,
            records_total=10,
            records_success=8,
            records_failed=2,
            error_details=errors,
        )

        assert mock_session.flush.called

    # ==================== 冲突检测测试 ====================

    def test_compare_data_no_conflict(self, engine: SyncEngine):
        """测试比较数据无冲突."""
        data_a = {"name": "项目A", "status": "active"}
        data_b = {"name": "项目A", "status": "active"}

        conflicts = engine._compare_data(data_a, data_b, ["id", "created_at", "updated_at"])

        assert len(conflicts) == 0

    def test_compare_data_with_difference(self, engine: SyncEngine):
        """测试比较数据有冲突."""
        data_a = {"name": "项目A", "status": "active", "updated_at": "2026-04-19T10:00:00"}
        data_b = {"name": "项目A", "status": "completed", "updated_at": "2026-04-19T11:00:00"}

        conflicts = engine._compare_data(data_a, data_b, ["id", "created_at", "updated_at"])

        assert len(conflicts) > 0
        assert "status" in conflicts

    def test_compare_data_with_timestamp(self, engine: SyncEngine):
        """测试比较数据包含时间戳."""
        data_a = {
            "name": "项目A",
            "status": "active",
            "updated_at": datetime(2026, 4, 19, 10, 0, 0, tzinfo=timezone.utc),
        }
        data_b = {
            "name": "项目A",
            "status": "completed",
            "updated_at": datetime(2026, 4, 19, 11, 0, 0, tzinfo=timezone.utc),
        }

        conflicts = engine._compare_data(data_a, data_b, ["id", "created_at"])

        assert len(conflicts) > 0
        # 检查时间戳是否被正确转换为可比值
        assert engine._make_comparable(data_a["updated_at"]) != engine._make_comparable(data_b["updated_at"])

    def test_detect_conflict_async(self, engine: SyncEngine, mock_session: MagicMock):
        """测试async版本的detect_conflict."""
        entity_id = uuid.uuid4()

        # Mock数据库操作
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        import asyncio
        result = asyncio.run(engine.detect_conflict(
            entity_type="project",
            entity_id=entity_id,
            source_a="lark_card",
            data_a={"name": "项目A", "status": "active"},
            source_b="lark_sheet",
            data_b={"name": "项目A", "status": "completed"},
        ))

        assert result is not None
        assert mock_session.add.called

    # ==================== 冲突解决测试 ====================

    @pytest.mark.asyncio
    async def test_resolve_conflict_last_write_strategy(self, engine: SyncEngine, mock_session: MagicMock):
        """测试最后写入优先策略."""
        conflict_id = uuid.uuid4()

        # Mock冲突记录
        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps({"name": "项目A", "status": "active", "updated_at": "2026-04-19T10:00:00"})
        mock_conflict.data_b = json.dumps({"name": "项目A", "status": "completed", "updated_at": "2026-04-19T11:00:00"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.LAST_WRITE,
        )

        # 时间戳B较晚，应选择data_b的值
        assert result.resolution_strategy == ConflictResolutionStrategy.LAST_WRITE
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_resolve_conflict_source_a_strategy(self, engine: SyncEngine, mock_session: MagicMock):
        """测试来源A优先策略."""
        conflict_id = uuid.uuid4()

        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps({"name": "项目A", "status": "active"})
        mock_conflict.data_b = json.dumps({"name": "项目A", "status": "completed"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.SOURCE_A,
        )

        resolved_data = json.loads(result.resolved_data)
        assert resolved_data.get("status") == "active"

    @pytest.mark.asyncio
    async def test_resolve_conflict_source_b_strategy(self, engine: SyncEngine, mock_session: MagicMock):
        """测试来源B优先策略."""
        conflict_id = uuid.uuid4()

        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps({"name": "项目A", "status": "active"})
        mock_conflict.data_b = json.dumps({"name": "项目A", "status": "completed"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.SOURCE_B,
        )

        resolved_data = json.loads(result.resolved_data)
        assert resolved_data.get("status") == "completed"

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual_strategy(self, engine: SyncEngine, mock_session: MagicMock):
        """测试人工解决策略."""
        conflict_id = uuid.uuid4()

        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps({"name": "项目A", "status": "active"})
        mock_conflict.data_b = json.dumps({"name": "项目A", "status": "completed"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.MANUAL,
            resolved_by_id="user_123",
            resolved_by_name="张三",
            resolution_notes="人工决定采用active状态",
        )

        assert result.resolution_status == "resolved"
        assert result.resolved_by_name == "张三"

    # ==================== 版本记录测试 ====================

    @pytest.mark.asyncio
    async def test_record_version_create(self, engine: SyncEngine, mock_session: MagicMock):
        """测试记录创建版本."""
        entity_id = uuid.uuid4()

        # 模拟查询返回None（无历史版本）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        mock_version = MagicMock()
        mock_version.id = uuid.uuid4()
        mock_version.version = 1
        mock_session.refresh.return_value = None

        result = await engine.record_version(
            entity_type="project",
            entity_id=entity_id,
            operation="create",
            data_after={"name": "新项目"},
            data_source="lark_card",
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_record_version_update(self, engine: SyncEngine, mock_session: MagicMock):
        """测试记录更新版本."""
        entity_id = uuid.uuid4()

        # 模拟查询返回现有版本号
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 2
        mock_session.execute.return_value = mock_result

        mock_version = MagicMock()
        mock_session.refresh.return_value = None

        result = await engine.record_version(
            entity_type="project",
            entity_id=entity_id,
            operation="update",
            data_before={"name": "旧项目"},
            data_after={"name": "新项目"},
            data_source="lark_sheet_sync",
        )

        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_record_version_with_lark_sheet_info(self, engine: SyncEngine, mock_session: MagicMock):
        """测试记录版本带飞书表格信息."""
        entity_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await engine.record_version(
            entity_type="task",
            entity_id=entity_id,
            operation="update",
            data_after={"name": "更新任务"},
            data_source="lark_sheet_sync",
            lark_sheet_token="sheet_token_123",
            lark_sheet_row=5,
        )

        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_get_version_history(self, engine: SyncEngine, mock_session: MagicMock):
        """测试查询版本历史."""
        entity_id = uuid.uuid4()

        # 模拟返回版本列表
        mock_versions = [MagicMock(version=3), MagicMock(version=2), MagicMock(version=1)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_versions
        mock_session.execute.return_value = mock_result

        history = await engine.get_version_history(
            entity_type="project",
            entity_id=entity_id,
            limit=20,
        )

        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, engine: SyncEngine, mock_session: MagicMock):
        """测试回滚到指定版本."""
        entity_id = uuid.uuid4()

        # 模拟查询返回版本
        mock_version = MagicMock()
        mock_version.data_after = json.dumps({"name": "历史版本名称"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_version
        mock_session.execute.return_value = mock_result

        data = await engine.rollback_to_version(
            entity_type="project",
            entity_id=entity_id,
            target_version=2,
        )

        assert data is not None
        assert data.get("name") == "历史版本名称"

    @pytest.mark.asyncio
    async def test_rollback_to_version_not_found(self, engine: SyncEngine, mock_session: MagicMock):
        """测试回滚版本不存在."""
        entity_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        data = await engine.rollback_to_version(
            entity_type="project",
            entity_id=entity_id,
            target_version=999,
        )

        assert data is None

    # ==================== 绑定配置测试 ====================

    @pytest.mark.asyncio
    async def test_get_lark_sheet_binding(self, engine: SyncEngine, mock_session: MagicMock):
        """测试获取飞书表格绑定配置."""
        binding_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = binding_id
        mock_binding.module = "task"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_binding
        mock_session.execute.return_value = mock_result

        binding = await engine.get_lark_sheet_binding(binding_id)

        assert binding is not None
        assert binding.module == "task"

    @pytest.mark.asyncio
    async def test_get_lark_sheet_binding_not_found(self, engine: SyncEngine, mock_session: MagicMock):
        """测试获取不存在的绑定配置."""
        binding_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        binding = await engine.get_lark_sheet_binding(binding_id)

        assert binding is None

    @pytest.mark.asyncio
    async def test_get_active_bindings(self, engine: SyncEngine, mock_session: MagicMock):
        """测试获取活跃绑定配置列表."""
        project_id = uuid.uuid4()

        mock_bindings = [MagicMock(module="task"), MagicMock(module="risk")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_bindings
        mock_session.execute.return_value = mock_result

        bindings = await engine.get_active_bindings(project_id=project_id)

        assert len(bindings) == 2

    @pytest.mark.asyncio
    async def test_get_active_bindings_with_filter(self, engine: SyncEngine, mock_session: MagicMock):
        """测试获取绑定配置列表带过滤."""
        project_id = uuid.uuid4()

        mock_bindings = [MagicMock(module="task")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_bindings
        mock_session.execute.return_value = mock_result

        bindings = await engine.get_active_bindings(
            project_id=project_id,
            module="task",
            sync_enabled=True,
        )

        assert len(bindings) == 1

    @pytest.mark.asyncio
    async def test_create_binding(self, engine: SyncEngine, mock_session: MagicMock):
        """测试创建绑定配置."""
        project_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = uuid.uuid4()
        mock_binding.project_id = project_id
        mock_binding.module = "task"
        mock_session.refresh.return_value = None

        binding = await engine.create_binding(
            project_id=project_id,
            module="task",
            lark_sheet_token="token_123",
            lark_sheet_id="sheet_456",
            field_mappings=json.dumps({"A": "name", "B": "status"}),
            sync_mode="bidirectional",
            sync_frequency="realtime",
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_create_binding_with_operator(self, engine: SyncEngine, mock_session: MagicMock):
        """测试创建绑定配置带操作人."""
        project_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_session.refresh.return_value = None

        binding = await engine.create_binding(
            project_id=project_id,
            module="task",
            lark_sheet_token="token_123",
            lark_sheet_id="sheet_456",
            field_mappings=json.dumps({"A": "name"}),
            operator_id="user_123",
            operator_name="张三",
        )

        assert mock_session.add.called

    @pytest.mark.asyncio
    async def test_update_binding_sync_status(self, engine: SyncEngine, mock_session: MagicMock):
        """测试更新绑定同步状态."""
        binding_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = binding_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_binding
        mock_session.execute.return_value = mock_result

        result = await engine.update_binding_sync_status(
            binding_id,
            SyncStatus.SUCCESS,
        )

        assert mock_session.flush.called

    @pytest.mark.asyncio
    async def test_delete_binding_success(self, engine: SyncEngine, mock_session: MagicMock):
        """测试删除绑定配置."""
        binding_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = binding_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_binding
        mock_session.execute.return_value = mock_result

        success = await engine.delete_binding(binding_id)

        assert success == True
        assert mock_session.delete.called

    @pytest.mark.asyncio
    async def test_delete_binding_not_found(self, engine: SyncEngine, mock_session: MagicMock):
        """测试删除不存在的绑定."""
        binding_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        success = await engine.delete_binding(binding_id)

        assert success == False

    @pytest.mark.asyncio
    async def test_toggle_binding_sync_enable(self, engine: SyncEngine, mock_session: MagicMock):
        """测试启用绑定同步."""
        binding_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = binding_id
        mock_binding.sync_enabled = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_binding
        mock_session.execute.return_value = mock_result

        result = await engine.toggle_binding_sync(binding_id, enabled=True)

        assert result is not None
        assert result.sync_enabled == True

    @pytest.mark.asyncio
    async def test_toggle_binding_sync_disable(self, engine: SyncEngine, mock_session: MagicMock):
        """测试禁用绑定同步."""
        binding_id = uuid.uuid4()

        mock_binding = MagicMock()
        mock_binding.id = binding_id
        mock_binding.sync_enabled = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_binding
        mock_session.execute.return_value = mock_result

        result = await engine.toggle_binding_sync(binding_id, enabled=False)

        assert result is not None
        assert result.sync_enabled == False


class TestSyncEngineHelperMethods:
    """SyncEngine辅助方法测试."""

    @pytest.fixture
    def engine(self) -> SyncEngine:
        """创建SyncEngine实例（无session）."""
        # 直接使用类方法测试，不需要session
        return SyncEngine(AsyncMock())

    def test_compute_changed_fields_create(self, engine: SyncEngine):
        """测试计算变更字段（创建操作）."""
        data_before = None
        data_after = {"name": "新项目", "status": "active"}

        changed = engine._compute_changed_fields(data_before, data_after)

        assert "name" in changed
        assert "status" in changed

    def test_compute_changed_fields_no_change(self, engine: SyncEngine):
        """测试计算变更字段（无变更）."""
        data_before = {"name": "项目", "status": "active"}
        data_after = {"name": "项目", "status": "active"}

        changed = engine._compute_changed_fields(data_before, data_after)

        assert len(changed) == 0

    def test_compute_changed_fields_with_change(self, engine: SyncEngine):
        """测试计算变更字段（有变更）."""
        data_before = {"name": "旧项目", "status": "active"}
        data_after = {"name": "新项目", "status": "completed"}

        changed = engine._compute_changed_fields(data_before, data_after)

        assert "name" in changed
        assert "status" in changed

    def test_compute_changed_fields_excludes_metadata(self, engine: SyncEngine):
        """测试计算变更字段排除元数据字段."""
        data_before = {"id": "123", "name": "项目", "created_at": "2026-01-01"}
        data_after = {"id": "123", "name": "项目", "created_at": "2026-04-19"}

        changed = engine._compute_changed_fields(data_before, data_after)

        # id和created_at不应在变更列表中
        assert "id" not in changed
        assert "created_at" not in changed

    def test_make_comparable_string(self, engine: SyncEngine):
        """测试转换为可比较值（字符串）."""
        result = engine._make_comparable("test")
        assert result == "test"

    def test_make_comparable_dict(self, engine: SyncEngine):
        """测试转换为可比较值（字典）."""
        result = engine._make_comparable({"key": "value"})
        # dict类型不转换，原样返回
        assert isinstance(result, dict)
        assert result == {"key": "value"}

    def test_make_comparable_none(self, engine: SyncEngine):
        """测试转换为可比较值（None）."""
        result = engine._make_comparable(None)
        assert result is None


class TestSyncEngineEdgeCases:
    """SyncEngine边界情况测试."""

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
    def engine(self, mock_session: MagicMock) -> SyncEngine:
        """创建SyncEngine实例."""
        return SyncEngine(mock_session)

    def test_compare_data_empty_data(self, engine: SyncEngine):
        """测试比较空数据."""
        data_a = {}
        data_b = {}

        conflicts = engine._compare_data(data_a, data_b, ["id", "created_at"])

        assert len(conflicts) == 0

    def test_compare_data_different_keys(self, engine: SyncEngine):
        """测试比较不同键的数据."""
        data_a = {"name": "项目A"}
        data_b = {"title": "项目B"}

        # 由于键不同，遍历data_a的键时，title不在data_a中
        conflicts = engine._compare_data(data_a, data_b, ["id", "created_at"])

        # name在data_a中存在，但在data_b中不存在（None），应检测到冲突
        assert len(conflicts) > 0

    @pytest.mark.asyncio
    async def test_resolve_conflict_missing_data_in_a(self, engine: SyncEngine, mock_session: MagicMock):
        """测试解决冲突缺少数据A."""
        conflict_id = uuid.uuid4()

        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps(None)
        mock_conflict.data_b = json.dumps({"name": "项目B"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.SOURCE_B,
        )

        resolved_data = json.loads(result.resolved_data)
        assert resolved_data.get("name") == "项目B"

    @pytest.mark.asyncio
    async def test_resolve_conflict_merge_strategy(self, engine: SyncEngine, mock_session: MagicMock):
        """测试合并策略."""
        conflict_id = uuid.uuid4()

        mock_conflict = MagicMock()
        mock_conflict.id = conflict_id
        mock_conflict.data_a = json.dumps({"name": "项目A", "status": "active"})
        mock_conflict.data_b = json.dumps({"name": "项目B", "priority": "high"})
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conflict
        mock_session.execute.return_value = mock_result

        result = await engine.resolve_conflict(
            conflict_id,
            ConflictResolutionStrategy.MERGE,
        )

        # MERGE策略目前默认选择来源B
        assert result is not None
        assert result.resolution_strategy == ConflictResolutionStrategy.MERGE

    @pytest.mark.asyncio
    async def test_get_active_bindings_empty(self, engine: SyncEngine, mock_session: MagicMock):
        """测试获取空绑定列表."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        bindings = await engine.get_active_bindings()

        assert len(bindings) == 0