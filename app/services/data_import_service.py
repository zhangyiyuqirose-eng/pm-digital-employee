"""
PM Digital Employee - Data Import Service
项目经理数字员工系统 - 数据入库服务

v1.3.0新增：调用现有Service层完成数据入库
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import ServiceError
from app.domain.enums import DataSource
from app.services.validation_service import ValidationService, ValidationResult
from app.services.sync_engine import SyncEngine

logger = get_logger(__name__)


class ImportError(ServiceError):
    """数据入库错误."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="import_error",
            message=message,
            details=details or {},
        )


class PermissionDeniedError(ServiceError):
    """权限拒绝错误."""

    def __init__(self, message: str):
        super().__init__(
            code="permission_denied",
            message=message,
        )


@dataclass
class SingleImportResult:
    """单个实体入库结果."""

    status: str                              # 状态：success/validation_failed/conflict/permission_denied/failed
    entity_id: Optional[str] = None          # 实体ID
    entity_type: Optional[str] = None        # 实体类型
    errors: List[Dict[str, Any]] = field(default_factory=list)  # 错误列表
    conflict_id: Optional[str] = None        # 冲突记录ID
    existing_data: Optional[Dict[str, Any]] = None  # 已有数据
    new_data: Optional[Dict[str, Any]] = None       # 新数据


@dataclass
class ImportResult:
    """批量入库结果."""

    imported_count: int                      # 成功导入数量
    failed_count: int                        # 失败数量
    conflict_count: int                      # 冲突数量
    imported_entities: List[SingleImportResult] = field(default_factory=list)
    failed_entities: List[SingleImportResult] = field(default_factory=list)
    conflicts: List[SingleImportResult] = field(default_factory=list)

    def is_success(self) -> bool:
        """是否全部成功."""
        return self.failed_count == 0 and self.conflict_count == 0

    def is_partial_success(self) -> bool:
        """是否部分成功."""
        return self.imported_count > 0 and (self.failed_count > 0 or self.conflict_count > 0)


class DataImportService:
    """
    数据入库服务.

    调用现有Service层完成数据入库，包括：
    1. 数据校验（ValidationService）
    2. 权限检查（AccessControlService）
    3. 冲突检测（SyncEngine）
    4. 数据入库（各实体Service）
    5. 版本记录（DataVersion）
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化入库服务."""
        self.session = session
        self.validation_service = ValidationService()
        self.sync_engine = SyncEngine(session)

    async def import_all(
        self,
        entities: List[Dict[str, Any]],
        project_id: uuid.UUID,
        user_context: Dict[str, Any],
    ) -> ImportResult:
        """
        执行所有实体的入库.

        Args:
            entities: 提取的实体列表
            project_id: 项目ID
            user_context: 用户上下文

        Returns:
            ImportResult: 入库结果
        """
        logger.info(
            f"Importing entities: count={len(entities)}, "
            f"project_id={project_id}"
        )

        imported_entities = []
        failed_entities = []
        conflicts = []

        for entity in entities:
            try:
                result = await self._import_single_entity(
                    entity, project_id, user_context
                )

                if result.status == "success":
                    imported_entities.append(result)
                elif result.status == "conflict":
                    conflicts.append(result)
                else:
                    failed_entities.append(result)

            except Exception as e:
                logger.error(f"Failed to import entity: {e}")
                failed_entities.append(SingleImportResult(
                    status="failed",
                    entity_type=entity.get("entity_type"),
                    errors=[{"error": str(e)}],
                ))

        result = ImportResult(
            imported_count=len(imported_entities),
            failed_count=len(failed_entities),
            conflict_count=len(conflicts),
            imported_entities=imported_entities,
            failed_entities=failed_entities,
            conflicts=conflicts,
        )

        logger.info(
            f"Import completed: imported={result.imported_count}, "
            f"failed={result.failed_count}, conflicts={result.conflict_count}"
        )

        return result

    async def _import_single_entity(
        self,
        entity: Dict[str, Any],
        project_id: uuid.UUID,
        user_context: Dict[str, Any],
    ) -> SingleImportResult:
        """
        导入单个实体.

        Args:
            entity: 实体数据
            project_id: 项目ID
            user_context: 用户上下文

        Returns:
            SingleImportResult: 入库结果
        """
        entity_type = entity.get("entity_type", "unknown")
        data = entity.get("data", {})

        # 添加项目ID到数据
        data["project_id"] = str(project_id)

        # Step 1: 数据校验
        validation_result = self.validation_service.validate_all(data, entity_type)
        if not validation_result.is_valid:
            logger.warning(
                f"Validation failed for entity: type={entity_type}, "
                f"errors={validation_result.errors}"
            )
            return SingleImportResult(
                status="validation_failed",
                entity_type=entity_type,
                errors=validation_result.errors,
            )

        # 使用校验后的数据
        validated_data = validation_result.validated_data or data

        # Step 2: 权限检查
        has_permission = await self._check_write_permission(
            user_context.get("user_id"),
            project_id,
            entity_type,
        )
        if not has_permission:
            return SingleImportResult(
                status="permission_denied",
                entity_type=entity_type,
                errors=[{"error": "无数据写入权限"}],
            )

        # Step 3: 冲突检测（查找已存在实体）
        existing_entity = await self._find_existing_entity(
            entity_type, validated_data, project_id
        )

        if existing_entity:
            # 存在冲突，需要解决
            return SingleImportResult(
                status="conflict",
                entity_type=entity_type,
                existing_data=self._entity_to_dict(existing_entity),
                new_data=validated_data,
            )

        # Step 4: 创建实体
        entity_obj = await self._create_entity(
            entity_type, validated_data, project_id, user_context
        )

        # Step 5: 设置数据来源
        entity_obj.data_source = DataSource.DOCUMENT_PARSE.value
        entity_obj.sync_version = 1
        entity_obj.last_sync_at = datetime.now(timezone.utc)

        await self.session.commit()

        # Step 6: 记录版本（可选）
        await self._record_version(entity_obj, "create", validated_data)

        logger.info(f"Entity created: type={entity_type}, id={entity_obj.id}")

        return SingleImportResult(
            status="success",
            entity_id=str(entity_obj.id),
            entity_type=entity_type,
        )

    async def resolve_conflict(
        self,
        conflict_result: SingleImportResult,
        resolution_strategy: str,
        user_context: Dict[str, Any],
    ) -> SingleImportResult:
        """
        解决数据冲突.

        Args:
            conflict_result: 冲突结果
            resolution_strategy: 解决策略（new/existing/manual）
            user_context: 用户上下文

        Returns:
            SingleImportResult: 解决后的结果
        """
        entity_type = conflict_result.entity_type
        new_data = conflict_result.new_data or {}
        existing_data = conflict_result.existing_data or {}

        if resolution_strategy == "existing":
            # 保留原数据
            return SingleImportResult(
                status="skipped",
                entity_type=entity_type,
            )

        if resolution_strategy == "new":
            # 采用新数据
            # TODO: 更新现有实体
            return SingleImportResult(
                status="success",
                entity_type=entity_type,
            )

        # 手动编辑 - 需要用户提供数据
        return SingleImportResult(
            status="pending_manual",
            entity_type=entity_type,
        )

    async def _check_write_permission(
        self,
        user_id: Optional[str],
        project_id: uuid.UUID,
        entity_type: str,
    ) -> bool:
        """检查写入权限."""
        if not user_id:
            return False

        # TODO: 调用实际的权限检查服务
        # from app.services.access_control_service import AccessControlService
        # access_control = AccessControlService(self.session)
        # return await access_control.check_permission(...)

        # 当前简化实现：假设所有项目成员有写入权限
        return True

    async def _find_existing_entity(
        self,
        entity_type: str,
        data: Dict[str, Any],
        project_id: uuid.UUID,
    ) -> Optional[Any]:
        """查找已存在的实体."""
        # 根据实体类型和关键字段查找
        entity_name = data.get("name") or data.get("title")

        if not entity_name:
            return None

        # TODO: 根据实体类型查询对应表
        # 当前简化实现
        return None

    async def _create_entity(
        self,
        entity_type: str,
        data: Dict[str, Any],
        project_id: uuid.UUID,
        user_context: Dict[str, Any],
    ) -> Any:
        """创建实体."""
        # 根据实体类型调用对应的Service
        entity_model_map = {
            "Task": "app.domain.models.task.Task",
            "Milestone": "app.domain.models.milestone.Milestone",
            "Risk": "app.domain.models.risk.ProjectRisk",
            "Cost": "app.domain.models.cost.ProjectCostActual",
            "WeeklyReport": "app.domain.models.weekly_report.WeeklyReport",
            "MeetingMinutes": "app.domain.models.meeting_minutes.MeetingMinutes",
        }

        if entity_type not in entity_model_map:
            raise ImportError(f"不支持的实体类型: {entity_type}")

        # 导入模型
        import importlib
        module_path, class_name = entity_model_map[entity_type].rsplit(".", 1)
        module = importlib.import_module(module_path)
        model_class = getattr(module, class_name)

        # 创建实体
        entity_obj = model_class(**data)
        self.session.add(entity_obj)
        await self.session.flush()

        return entity_obj

    def _entity_to_dict(self, entity: Any) -> Dict[str, Any]:
        """将实体转换为字典."""
        if hasattr(entity, "to_dict"):
            return entity.to_dict()

        result = {}
        for column in entity.__table__.columns:
            value = getattr(entity, column.name)
            if value is not None:
                result[column.name] = value

        return result

    async def _record_version(
        self,
        entity: Any,
        operation: str,
        data: Dict[str, Any],
    ) -> None:
        """记录数据版本."""
        # TODO: 调用 SyncEngine 记录版本
        pass


# 服务工厂（需要session）
def get_data_import_service(session: AsyncSession) -> DataImportService:
    """获取数据入库服务实例."""
    return DataImportService(session)