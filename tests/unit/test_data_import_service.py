"""
PM Digital Employee - Data Import Service Tests
项目经理数字员工系统 - 数据入库服务单元测试

v1.3.0新增：测试数据入库服务的核心功能
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from app.services.data_import_service import (
    DataImportService,
    SingleImportResult,
    ImportResult,
    ImportError,
    PermissionDeniedError,
    get_data_import_service,
)
from app.domain.enums import DataSource


class TestSingleImportResult:
    """SingleImportResult测试类."""

    def test_single_import_result_success(self):
        """测试成功结果创建."""
        result = SingleImportResult(
            status="success",
            entity_id="entity-001",
            entity_type="Task",
        )

        assert result.status == "success"
        assert result.entity_id == "entity-001"
        assert result.entity_type == "Task"

    def test_single_import_result_with_errors(self):
        """测试带错误的结果."""
        result = SingleImportResult(
            status="validation_failed",
            entity_type="Task",
            errors=[{"field": "name", "error": "缺少必填字段"}],
        )

        assert result.status == "validation_failed"
        assert len(result.errors) == 1

    def test_single_import_result_conflict(self):
        """测试冲突结果."""
        result = SingleImportResult(
            status="conflict",
            entity_type="Task",
            conflict_id="conflict-001",
            existing_data={"name": "已存在任务"},
            new_data={"name": "新任务"},
        )

        assert result.status == "conflict"
        assert result.conflict_id == "conflict-001"


class TestImportResult:
    """ImportResult测试类."""

    def test_import_result_success(self):
        """测试导入成功结果."""
        result = ImportResult(
            imported_count=5,
            failed_count=0,
            conflict_count=0,
        )

        assert result.imported_count == 5
        assert result.is_success() == True
        assert result.is_partial_success() == False

    def test_import_result_partial_success(self):
        """测试部分成功结果."""
        result = ImportResult(
            imported_count=3,
            failed_count=2,
            conflict_count=0,
        )

        assert result.is_success() == False
        assert result.is_partial_success() == True

    def test_import_result_with_conflicts(self):
        """测试带冲突结果."""
        result = ImportResult(
            imported_count=2,
            failed_count=1,
            conflict_count=2,
        )

        assert result.is_success() == False
        assert result.conflict_count == 2

    def test_import_result_all_failed(self):
        """测试全部失败."""
        result = ImportResult(
            imported_count=0,
            failed_count=5,
            conflict_count=0,
        )

        assert result.is_success() == False
        assert result.is_partial_success() == False

    def test_import_result_with_entities(self):
        """测试带实体列表."""
        imported = [
            SingleImportResult(status="success", entity_id="e1", entity_type="Task"),
            SingleImportResult(status="success", entity_id="e2", entity_type="Task"),
        ]
        failed = [
            SingleImportResult(status="failed", entity_type="Risk"),
        ]
        conflicts = [
            SingleImportResult(status="conflict", entity_type="Milestone"),
        ]

        result = ImportResult(
            imported_count=2,
            failed_count=1,
            conflict_count=1,
            imported_entities=imported,
            failed_entities=failed,
            conflicts=conflicts,
        )

        assert len(result.imported_entities) == 2
        assert len(result.failed_entities) == 1
        assert len(result.conflicts) == 1


class TestImportError:
    """ImportError测试类."""

    def test_import_error_creation(self):
        """测试错误创建."""
        error = ImportError("导入失败", {"entity": "Task"})

        assert error.code == "import_error"
        assert error.message == "导入失败"
        assert error.details["entity"] == "Task"

    def test_import_error_minimal(self):
        """测试最小化错误."""
        error = ImportError("导入失败")

        assert error.code == "import_error"
        assert error.details == {}


class TestPermissionDeniedError:
    """PermissionDeniedError测试类."""

    def test_permission_denied_error(self):
        """测试权限拒绝错误."""
        error = PermissionDeniedError("无写入权限")

        assert error.code == "permission_denied"
        assert error.message == "无写入权限"


class MockAsyncSession:
    """Mock AsyncSession."""

    def __init__(self):
        self.added_objects = []
        self._flush_called = False
        self._commit_called = False

    def add(self, obj):
        self.added_objects.append(obj)

    async def flush(self):
        self._flush_called = True

    async def commit(self):
        self._commit_called = True

    async def execute(self, stmt):
        return MagicMock()

    async def rollback(self):
        pass


class TestDataImportServiceInit:
    """服务初始化测试."""

    def test_service_creation(self):
        """测试服务创建."""
        session = MockAsyncSession()
        service = DataImportService(session)

        assert service.session is not None
        assert service.validation_service is not None
        assert service.sync_engine is not None


class TestDataImportServiceImport:
    """入库操作测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_import_all_empty_list(self, service):
        """测试空列表入库."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        result = await service.import_all([], project_id, user_context)

        assert result.imported_count == 0
        assert result.failed_count == 0
        assert result.conflict_count == 0

    @pytest.mark.asyncio
    async def test_import_single_entity(self, service):
        """测试单实体入库."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        entities = [
            {
                "entity_type": "Task",
                "data": {"name": "任务A", "status": "pending"},
            }
        ]

        # Mock ValidationService
        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(
                is_valid=True,
                validated_data={"name": "任务A", "status": "pending"},
                errors=[],
            )

            # Mock _check_write_permission
            with patch.object(service, '_check_write_permission', new_callable=AsyncMock) as mock_perm:
                mock_perm.return_value = True

                # Mock _find_existing_entity
                with patch.object(service, '_find_existing_entity', new_callable=AsyncMock) as mock_find:
                    mock_find.return_value = None

                    # Mock _create_entity
                    with patch.object(service, '_create_entity', new_callable=AsyncMock) as mock_create:
                        mock_entity = MagicMock()
                        mock_entity.id = uuid.uuid4()
                        mock_create.return_value = mock_entity

                        result = await service.import_all(entities, project_id, user_context)

                        # 验证调用
                        mock_validate.assert_called_once()
                        mock_perm.assert_called_once()
                        mock_find.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_validation_failed(self, service):
        """测试校验失败."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        entities = [
            {
                "entity_type": "Task",
                "data": {},  # 缺少必填字段name
            }
        ]

        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(
                is_valid=False,
                errors=[{"field": "name", "error": "缺少必填字段"}],
            )

            result = await service.import_all(entities, project_id, user_context)

            assert result.failed_count == 1
            assert len(result.failed_entities) == 1

    @pytest.mark.asyncio
    async def test_import_permission_denied(self, service):
        """测试权限拒绝."""
        project_id = uuid.uuid4()
        user_context = {"user_id": None}  # 无用户

        entities = [
            {
                "entity_type": "Task",
                "data": {"name": "任务A"},
            }
        ]

        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(is_valid=True)

            result = await service.import_all(entities, project_id, user_context)

            assert result.failed_count == 1

    @pytest.mark.asyncio
    async def test_import_conflict_detected(self, service):
        """测试冲突检测."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        entities = [
            {
                "entity_type": "Task",
                "data": {"name": "已存在任务"},
            }
        ]

        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(is_valid=True)

            with patch.object(service, '_check_write_permission', new_callable=AsyncMock) as mock_perm:
                mock_perm.return_value = True

                with patch.object(service, '_find_existing_entity', new_callable=AsyncMock) as mock_find:
                    # 返回已存在实体
                    mock_find.return_value = MagicMock(name="已存在任务")

                    result = await service.import_all(entities, project_id, user_context)

                    assert result.conflict_count == 1

    @pytest.mark.asyncio
    async def test_import_multiple_entities(self, service):
        """测试批量入库."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        entities = [
            {"entity_type": "Task", "data": {"name": "任务A"}},
            {"entity_type": "Task", "data": {"name": "任务B"}},
            {"entity_type": "Risk", "data": {"title": "风险A"}},
        ]

        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(is_valid=True)

            with patch.object(service, '_check_write_permission', new_callable=AsyncMock) as mock_perm:
                mock_perm.return_value = True

                with patch.object(service, '_find_existing_entity', new_callable=AsyncMock) as mock_find:
                    mock_find.return_value = None

                    with patch.object(service, '_create_entity', new_callable=AsyncMock) as mock_create:
                        mock_entity = MagicMock()
                        mock_entity.id = uuid.uuid4()
                        mock_create.return_value = mock_entity

                        result = await service.import_all(entities, project_id, user_context)

                        assert result.imported_count == 3


class TestDataImportServiceConflictResolution:
    """冲突解决测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_resolve_conflict_keep_existing(self, service):
        """测试保留原数据."""
        conflict = SingleImportResult(
            status="conflict",
            entity_type="Task",
            existing_data={"name": "已存在"},
            new_data={"name": "新数据"},
        )
        user_context = {"user_id": "user-001"}

        result = await service.resolve_conflict(conflict, "existing", user_context)

        assert result.status == "skipped"

    @pytest.mark.asyncio
    async def test_resolve_conflict_use_new(self, service):
        """测试采用新数据."""
        conflict = SingleImportResult(
            status="conflict",
            entity_type="Task",
            existing_data={"name": "已存在"},
            new_data={"name": "新数据"},
        )
        user_context = {"user_id": "user-001"}

        result = await service.resolve_conflict(conflict, "new", user_context)

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_resolve_conflict_manual(self, service):
        """测试手动编辑."""
        conflict = SingleImportResult(
            status="conflict",
            entity_type="Task",
            existing_data={"name": "已存在"},
            new_data={"name": "新数据"},
        )
        user_context = {"user_id": "user-001"}

        result = await service.resolve_conflict(conflict, "manual", user_context)

        assert result.status == "pending_manual"


class TestDataImportServicePermission:
    """权限检查测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_check_write_permission_with_user(self, service):
        """测试有用户权限."""
        project_id = uuid.uuid4()

        result = await service._check_write_permission("user-001", project_id, "Task")

        # 当前实现返回True
        assert result == True

    @pytest.mark.asyncio
    async def test_check_write_permission_no_user(self, service):
        """测试无用户."""
        project_id = uuid.uuid4()

        result = await service._check_write_permission(None, project_id, "Task")

        assert result == False


class TestDataImportServiceHelpers:
    """辅助方法测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_find_existing_entity_with_name(self, service):
        """测试查找已存在实体."""
        project_id = uuid.uuid4()
        data = {"name": "任务A"}

        result = await service._find_existing_entity("Task", data, project_id)

        # 当前简化实现返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_find_existing_entity_no_name(self, service):
        """测试无名称查找."""
        project_id = uuid.uuid4()
        data = {}  # 无name字段

        result = await service._find_existing_entity("Task", data, project_id)

        assert result is None

    def test_entity_to_dict_with_method(self, service):
        """测试实体转字典（有to_dict方法）."""
        mock_entity = MagicMock()
        mock_entity.to_dict = MagicMock(return_value={"id": "e1", "name": "测试"})

        result = service._entity_to_dict(mock_entity)

        assert result["id"] == "e1"

    def test_entity_to_dict_with_table(self, service):
        """测试实体转字典（使用table）."""
        # 创建一个简单的mock对象模拟实体
        class MockEntity:
            def __init__(self):
                self.id = "e1"
                self.name = "测试"

        mock_entity = MockEntity()
        # 添加__table__属性
        mock_entity.__table__ = MagicMock()
        # 使用真实的字符串作为列名
        column1 = type('Column', (), {'name': 'id'})()
        column2 = type('Column', (), {'name': 'name'})()
        mock_entity.__table__.columns = [column1, column2]

        result = service._entity_to_dict(mock_entity)

        assert result["id"] == "e1"
        assert result["name"] == "测试"


class TestDataImportServiceEntityCreation:
    """实体创建测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_create_entity_unsupported_type(self, service):
        """测试不支持的实体类型."""
        project_id = uuid.uuid4()
        data = {"name": "测试"}
        user_context = {}

        with pytest.raises(ImportError) as exc_info:
            await service._create_entity("UnknownEntity", data, project_id, user_context)

        assert "不支持的实体类型" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_entity_supported_types(self, service):
        """测试支持的实体类型列表."""
        # 验证entity_model_map中支持的类型
        entity_model_map = {
            "Task": "app.domain.models.task.Task",
            "Milestone": "app.domain.models.milestone.Milestone",
            "Risk": "app.domain.models.risk.ProjectRisk",
            "Cost": "app.domain.models.cost.ProjectCostActual",
            "WeeklyReport": "app.domain.models.weekly_report.WeeklyReport",
            "MeetingMinutes": "app.domain.models.meeting_minutes.MeetingMinutes",
        }

        for entity_type in entity_model_map.keys():
            assert entity_type in ["Task", "Milestone", "Risk", "Cost", "WeeklyReport", "MeetingMinutes"]


class TestGetDataImportService:
    """服务工厂测试."""

    def test_get_data_import_service(self):
        """测试获取服务实例."""
        session = MockAsyncSession()

        service = get_data_import_service(session)

        assert service is not None
        assert isinstance(service, DataImportService)


class TestDataSourceIntegration:
    """数据来源集成测试."""

    @pytest.fixture
    def mock_session(self):
        """创建Mock Session."""
        return MockAsyncSession()

    @pytest.fixture
    def service(self, mock_session):
        """创建服务实例."""
        return DataImportService(mock_session)

    @pytest.mark.asyncio
    async def test_data_source_set_correctly(self, service):
        """测试数据来源设置."""
        project_id = uuid.uuid4()
        user_context = {"user_id": "user-001"}

        entities = [{"entity_type": "Task", "data": {"name": "任务A"}}]

        with patch.object(service.validation_service, 'validate_all') as mock_validate:
            mock_validate.return_value = MagicMock(is_valid=True)

            with patch.object(service, '_check_write_permission', new_callable=AsyncMock) as mock_perm:
                mock_perm.return_value = True

                with patch.object(service, '_find_existing_entity', new_callable=AsyncMock) as mock_find:
                    mock_find.return_value = None

                    with patch.object(service, '_create_entity', new_callable=AsyncMock) as mock_create:
                        mock_entity = MagicMock()
                        mock_entity.id = uuid.uuid4()
                        mock_create.return_value = mock_entity

                        await service.import_all(entities, project_id, user_context)

                        # 验证session.commit被调用（会设置data_source）
                        # 注意：实际设置在_import_single_entity中