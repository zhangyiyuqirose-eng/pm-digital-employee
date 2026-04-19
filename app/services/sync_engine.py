"""
PM Digital Employee - Sync Engine
项目经理数字员工系统 - 数据同步引擎

v1.2.0新增：提供统一的数据同步状态管理、冲突检测和解决、版本记录功能。

支持三种数据来源的同步：
1. 飞书卡片录入 (lark_card)
2. Excel模板导入 (excel_import)
3. 飞书在线表格同步 (lark_sheet_sync)

核心功能：
- 同步状态管理（创建/更新日志、状态追踪）
- 冲突检测（数据比较、差异识别）
- 冲突解决（多策略支持）
- 版本记录（每次变更记录、回滚支持）
- 绑定配置管理（飞书表格绑定配置）
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import DataNotFoundError, DatabaseError
from app.domain.models.data_conflict import DataConflict
from app.domain.models.data_version import DataVersion
from app.domain.models.data_sync_log import DataSyncLog
from app.domain.models.lark_sheet_binding import LarkSheetBinding

logger = get_logger(__name__)


class SyncStatus:
    """同步状态枚举."""

    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    SUCCESS = "success"       # 成功
    FAILED = "failed"         # 失败
    PARTIAL = "partial"       # 部分 success


class ConflictResolutionStrategy:
    """冲突解决策略枚举."""

    LAST_WRITE = "last_write"     # 最后写入优先（按时间戳）
    SOURCE_A = "source_a"         # 来源A优先
    SOURCE_B = "source_b"         # 来源B优先
    MANUAL = "manual"             # 人工解决
    MERGE = "merge"               # 合并策略


class SyncEngine:
    """
    数据同步引擎.

    提供同步状态管理、冲突检测和解决、版本记录、同步日志等核心功能。
    作为多源数据录入的基础设施，确保数据一致性和可追溯性。
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        初始化同步引擎.

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== 同步状态管理 ====================

    async def create_sync_log(
        self,
        sync_type: str,
        sync_direction: str,
        module: str,
        project_id: Optional[uuid.UUID] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        lark_sheet_token: Optional[str] = None,
        excel_file_name: Optional[str] = None,
    ) -> DataSyncLog:
        """
        创建同步日志记录.

        Args:
            sync_type: 同步类型（excel_import/lark_sheet/lark_card）
            sync_direction: 同步方向（import/export/bidirectional）
            module: 功能模块
            project_id: 项目ID
            operator_id: 操作人ID
            operator_name: 操作人姓名
            lark_sheet_token: 飞书表格Token
            excel_file_name: Excel文件名

        Returns:
            DataSyncLog: 同步日志对象
        """
        sync_log = DataSyncLog(
            id=uuid.uuid4(),
            sync_type=sync_type,
            sync_direction=sync_direction,
            sync_status=SyncStatus.PENDING,
            module=module,
            project_id=project_id,
            operator_id=operator_id,
            operator_name=operator_name,
            lark_sheet_token=lark_sheet_token,
            excel_file_name=excel_file_name,
            records_total=0,
            records_success=0,
            records_failed=0,
            records_skipped=0,
            started_at=datetime.now(timezone.utc),
        )

        self.session.add(sync_log)
        await self.session.flush()

        logger.info(
            f"Sync log created: id={sync_log.id}, type={sync_type}, module={module}"
        )

        return sync_log

    async def update_sync_status(
        self,
        log_id: uuid.UUID,
        status: str,
        records_total: Optional[int] = None,
        records_success: Optional[int] = None,
        records_failed: Optional[int] = None,
        records_skipped: Optional[int] = None,
        error_details: Optional[List[Dict]] = None,
    ) -> DataSyncLog:
        """
        更新同步状态.

        Args:
            log_id: 同步日志ID
            status: 同步状态
            records_total: 总记录数
            records_success: 成功记录数
            records_failed: 失败记录数
            records_skipped: 跳过记录数
            error_details: 错误详情

        Returns:
            DataSyncLog: 更新后的同步日志
        """
        result = await self.session.execute(
            select(DataSyncLog).where(DataSyncLog.id == log_id)
        )
        sync_log = result.scalar_one_or_none()

        if not sync_log:
            raise ValueError(f"Sync log not found: {log_id}")

        # 更新状态
        sync_log.sync_status = status

        if records_total is not None:
            sync_log.records_total = records_total
        if records_success is not None:
            sync_log.records_success = records_success
        if records_failed is not None:
            sync_log.records_failed = records_failed
        if records_skipped is not None:
            sync_log.records_skipped = records_skipped
        if error_details:
            sync_log.error_details = json.dumps(error_details[:500])  # 限制大小

        # 计算耗时
        if status in [SyncStatus.SUCCESS, SyncStatus.FAILED, SyncStatus.PARTIAL]:
            sync_log.completed_at = datetime.now(timezone.utc)
            if sync_log.started_at:
                duration = sync_log.completed_at - sync_log.started_at
                sync_log.duration_ms = int(duration.total_seconds() * 1000)

        await self.session.flush()
        await self.session.refresh(sync_log)

        logger.info(
            f"Sync status updated: id={log_id}, status={status}, "
            f"success={sync_log.records_success}, failed={sync_log.records_failed}"
        )

        return sync_log

    async def get_sync_logs(
        self,
        project_id: Optional[uuid.UUID] = None,
        module: Optional[str] = None,
        sync_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[DataSyncLog]:
        """
        查询同步日志列表.

        Args:
            project_id: 项目ID过滤
            module: 模块过滤
            sync_type: 同步类型过滤
            limit: 返回数量限制

        Returns:
            List[DataSyncLog]: 同步日志列表
        """
        query = select(DataSyncLog).order_by(DataSyncLog.created_at.desc())

        if project_id:
            query = query.where(DataSyncLog.project_id == project_id)
        if module:
            query = query.where(DataSyncLog.module == module)
        if sync_type:
            query = query.where(DataSyncLog.sync_type == sync_type)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== 冲突检测和解决 ====================

    async def detect_conflict(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        source_a: str,
        data_a: Dict[str, Any],
        source_b: str,
        data_b: Dict[str, Any],
        ignore_fields: Optional[List[str]] = None,
    ) -> Optional[DataConflict]:
        """
        检测数据冲突.

        比较两个数据源的数据，发现不一致时记录冲突。

        Args:
            entity_type: 实体类型（project/task/cost等）
            entity_id: 实体ID
            source_a: 来源A标识
            data_a: 来源A的数据
            source_b: 来源B标识
            data_b: 来源B的数据
            ignore_fields: 忽略比较的字段列表

        Returns:
            Optional[DataConflict]: 如果存在冲突返回冲突记录，否则返回None
        """
        ignore_fields = ignore_fields or [
            "id", "created_at", "updated_at", "sync_version",
            "last_sync_at", "data_source", "external_id"
        ]

        # 比较两个数据源
        conflicts = self._compare_data(data_a, data_b, ignore_fields)

        if not conflicts:
            logger.debug(
                f"No conflict detected: entity={entity_type}:{entity_id}"
            )
            return None

        # 创建冲突记录
        conflict = DataConflict(
            id=uuid.uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            source_a=source_a,
            source_b=source_b,
            data_a=json.dumps(data_a, default=str),
            data_b=json.dumps(data_b, default=str),
            conflict_time=datetime.now(timezone.utc),
            resolution_status="pending",
        )

        self.session.add(conflict)
        await self.session.flush()

        logger.warning(
            f"Conflict detected: entity={entity_type}:{entity_id}, "
            f"conflicted_fields={list(conflicts.keys())}"
        )

        return conflict

    def _compare_data(
        self,
        data_a: Dict[str, Any],
        data_b: Dict[str, Any],
        ignore_fields: List[str],
    ) -> Dict[str, Tuple[Any, Any]]:
        """
        比较两个数据字典.

        Args:
            data_a: 数据A
            data_b: 数据B
            ignore_fields: 忽略的字段

        Returns:
            Dict: 冲突字段及其在两个数据源中的值
        """
        conflicts = {}

        for key in data_a.keys():
            if key in ignore_fields:
                continue

            value_a = data_a.get(key)
            value_b = data_b.get(key)

            # 转换为可比值（处理UUID、datetime等）
            comparable_a = self._make_comparable(value_a)
            comparable_b = self._make_comparable(value_b)

            if comparable_a != comparable_b:
                conflicts[key] = (value_a, value_b)

        return conflicts

    def _make_comparable(self, value: Any) -> Any:
        """
        将值转换为可比形式.

        Args:
            value: 原始值

        Returns:
            可比的值（字符串或数值）
        """
        if value is None:
            return None

        if isinstance(value, uuid.UUID):
            return str(value)

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")

        return value

    async def resolve_conflict(
        self,
        conflict_id: uuid.UUID,
        strategy: str,
        resolved_by_id: Optional[str] = None,
        resolved_by_name: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> DataConflict:
        """
        解决数据冲突.

        Args:
            conflict_id: 冲突记录ID
            strategy: 解决策略（last_write/source_a/source_b/manual）
            resolved_by_id: 解决人ID
            resolved_by_name: 解决人姓名
            resolution_notes: 解决备注

        Returns:
            DataConflict: 解决后的冲突记录
        """
        result = await self.session.execute(
            select(DataConflict).where(DataConflict.id == conflict_id)
        )
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise ValueError(f"Conflict not found: {conflict_id}")

        # 根据策略选择最终数据
        data_a = json.loads(conflict.data_a)
        data_b = json.loads(conflict.data_b)

        if strategy == ConflictResolutionStrategy.SOURCE_A:
            resolved_data = data_a
        elif strategy == ConflictResolutionStrategy.SOURCE_B:
            resolved_data = data_b
        elif strategy == ConflictResolutionStrategy.LAST_WRITE:
            # 比较时间戳，选择最新的数据
            time_a = data_a.get("updated_at") or data_a.get("last_sync_at")
            time_b = data_b.get("updated_at") or data_b.get("last_sync_at")

            if time_a and time_b:
                resolved_data = data_a if time_a >= time_b else data_b
            else:
                resolved_data = data_b  # 默认选择来源B
        elif strategy == ConflictResolutionStrategy.MANUAL:
            # 人工解决需要提供resolved_data
            resolved_data = None
        else:
            resolved_data = data_b  # 默认选择来源B

        # 更新冲突记录
        conflict.resolution_status = "resolved"
        conflict.resolution_strategy = strategy
        conflict.resolved_data = json.dumps(resolved_data, default=str) if resolved_data else None
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by_id = resolved_by_id
        conflict.resolved_by_name = resolved_by_name
        conflict.resolution_notes = resolution_notes

        await self.session.flush()
        await self.session.refresh(conflict)

        logger.info(
            f"Conflict resolved: id={conflict_id}, strategy={strategy}, "
            f"resolved_by={resolved_by_name}"
        )

        return conflict

    async def get_pending_conflicts(
        self,
        entity_type: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[DataConflict]:
        """
        查询待解决的冲突列表.

        Args:
            entity_type: 实体类型过滤
            project_id: 项目ID过滤（通过entity_id关联）
            limit: 返回数量限制

        Returns:
            List[DataConflict]: 待解决的冲突列表
        """
        query = select(DataConflict).where(
            DataConflict.resolution_status == "pending"
        ).order_by(DataConflict.conflict_time.desc())

        if entity_type:
            query = query.where(DataConflict.entity_type == entity_type)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ==================== 版本记录 ====================

    async def record_version(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        operation: str,
        data_before: Optional[Dict[str, Any]] = None,
        data_after: Optional[Dict[str, Any]] = None,
        data_source: str = "unknown",
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        lark_sheet_token: Optional[str] = None,
        lark_sheet_row: Optional[int] = None,
    ) -> DataVersion:
        """
        记录数据版本.

        每次数据变更都记录版本，支持历史追溯和回滚。

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            operation: 操作类型（create/update/delete）
            data_before: 操作前数据
            data_after: 操作后数据
            data_source: 数据来源
            operator_id: 操作人ID
            operator_name: 操作人姓名
            lark_sheet_token: 飞书表格Token
            lark_sheet_row: 飞书表格行号

        Returns:
            DataVersion: 版本记录对象
        """
        # 获取当前最大版本号
        max_version = await self._get_max_version(entity_type, entity_id)
        new_version = max_version + 1

        # 计算变更字段
        changed_fields = self._compute_changed_fields(data_before, data_after)

        version = DataVersion(
            id=uuid.uuid4(),
            entity_type=entity_type,
            entity_id=entity_id,
            version=new_version,
            operation=operation,
            data_before=json.dumps(data_before, default=str) if data_before else None,
            data_after=json.dumps(data_after, default=str) if data_after else None,
            changed_fields=json.dumps(changed_fields) if changed_fields else None,
            data_source=data_source,
            operator_id=operator_id,
            operator_name=operator_name,
            lark_sheet_token=lark_sheet_token,
            lark_sheet_row=lark_sheet_row,
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(version)
        await self.session.flush()

        logger.info(
            f"Version recorded: entity={entity_type}:{entity_id}, "
            f"version={new_version}, operation={operation}"
        )

        return version

    async def _get_max_version(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> int:
        """
        获取实体的最大版本号.

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            int: 最大版本号，如果没有版本记录返回0
        """
        result = await self.session.execute(
            select(func.max(DataVersion.version)).where(
                and_(
                    DataVersion.entity_type == entity_type,
                    DataVersion.entity_id == entity_id,
                )
            )
        )
        max_version = result.scalar_one_or_none()
        return max_version or 0

    def _compute_changed_fields(
        self,
        data_before: Optional[Dict[str, Any]],
        data_after: Optional[Dict[str, Any]],
    ) -> List[str]:
        """
        计算变更的字段列表.

        Args:
            data_before: 操作前数据
            data_after: 操作后数据

        Returns:
            List[str]: 变更的字段名列表
        """
        if not data_before and not data_after:
            return []

        if not data_before:
            return list(data_after.keys()) if data_after else []

        if not data_after:
            return list(data_before.keys()) if data_before else []

        changed = []
        for key in set(list(data_before.keys()) + list(data_after.keys())):
            if key in ["id", "created_at", "updated_at"]:
                continue

            value_before = self._make_comparable(data_before.get(key))
            value_after = self._make_comparable(data_after.get(key))

            if value_before != value_after:
                changed.append(key)

        return changed

    async def get_version_history(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        limit: int = 20,
    ) -> List[DataVersion]:
        """
        查询版本历史.

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            limit: 返回数量限制

        Returns:
            List[DataVersion]: 版本历史列表
        """
        query = select(DataVersion).where(
            and_(
                DataVersion.entity_type == entity_type,
                DataVersion.entity_id == entity_id,
            )
        ).order_by(DataVersion.version.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def rollback_to_version(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        target_version: int,
    ) -> Optional[Dict[str, Any]]:
        """
        回滚到指定版本.

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            target_version: 目标版本号

        Returns:
            Optional[Dict]: 回滚后的数据，如果版本不存在返回None
        """
        result = await self.session.execute(
            select(DataVersion).where(
                and_(
                    DataVersion.entity_type == entity_type,
                    DataVersion.entity_id == entity_id,
                    DataVersion.version == target_version,
                )
            )
        )
        version = result.scalar_one_or_none()

        if not version:
            logger.warning(
                f"Version not found for rollback: entity={entity_type}:{entity_id}, "
                f"version={target_version}"
            )
            return None

        # 返回该版本的数据
        if version.data_after:
            return json.loads(version.data_after)

        return None

    # ==================== 同步绑定管理 ====================

    async def get_lark_sheet_binding(
        self,
        binding_id: uuid.UUID,
    ) -> Optional[LarkSheetBinding]:
        """
        获取飞书表格绑定配置.

        Args:
            binding_id: 绑定配置ID

        Returns:
            Optional[LarkSheetBinding]: 绑定配置或None
        """
        result = await self.session.execute(
            select(LarkSheetBinding).where(LarkSheetBinding.id == binding_id)
        )
        return result.scalar_one_or_none()

    async def get_active_bindings(
        self,
        project_id: Optional[uuid.UUID] = None,
        module: Optional[str] = None,
        sync_enabled: Optional[bool] = None,
    ) -> List[LarkSheetBinding]:
        """
        获取项目的活跃绑定配置列表.

        Args:
            project_id: 项目ID（可选）
            module: 模块过滤（可选）
            sync_enabled: 同步启用状态过滤（可选）

        Returns:
            List[LarkSheetBinding]: 活跃的绑定配置列表
        """
        conditions = [LarkSheetBinding.status == "active"]

        if project_id:
            conditions.append(LarkSheetBinding.project_id == project_id)

        if module:
            conditions.append(LarkSheetBinding.module == module)

        if sync_enabled is not None:
            conditions.append(LarkSheetBinding.sync_enabled == sync_enabled)

        query = select(LarkSheetBinding).where(and_(*conditions))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_binding_sync_status(
        self,
        binding_id: uuid.UUID,
        sync_status: str,
        sync_time: Optional[datetime] = None,
    ) -> LarkSheetBinding:
        """
        更新绑定配置的同步状态.

        Args:
            binding_id: 绑定配置ID
            sync_status: 同步状态
            sync_time: 同步时间

        Returns:
            LarkSheetBinding: 更新后的绑定配置
        """
        result = await self.session.execute(
            select(LarkSheetBinding).where(LarkSheetBinding.id == binding_id)
        )
        binding = result.scalar_one_or_none()

        if not binding:
            raise ValueError(f"Binding not found: {binding_id}")

        binding.last_sync_status = sync_status
        binding.last_sync_at = sync_time or datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(binding)

        return binding

    async def create_binding(
        self,
        project_id: uuid.UUID,
        module: str,
        lark_sheet_token: str,
        lark_sheet_id: str,
        field_mappings: str,
        sync_mode: str = "bidirectional",
        sync_frequency: str = "realtime",
        data_range_start: Optional[str] = None,
        data_range_end: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> LarkSheetBinding:
        """
        创建飞书表格绑定配置.

        Args:
            project_id: 项目ID
            module: 模块名称
            lark_sheet_token: 飞书表格Token
            lark_sheet_id: 飞书Sheet ID
            field_mappings: 字段映射配置（JSON字符串）
            sync_mode: 同步模式
            sync_frequency: 同步频率
            data_range_start: 数据起始范围
            data_range_end: 数据结束范围
            operator_id: 操作人ID
            operator_name: 操作人姓名

        Returns:
            LarkSheetBinding: 创建的绑定配置
        """
        binding = LarkSheetBinding(
            id=uuid.uuid4(),
            project_id=project_id,
            module=module,
            lark_sheet_token=lark_sheet_token,
            lark_sheet_id=lark_sheet_id,
            field_mappings=field_mappings,
            sync_mode=sync_mode,
            sync_frequency=sync_frequency,
            data_range_start=data_range_start,
            data_range_end=data_range_end,
            sync_enabled=True,
            status="active",
            created_by_id=operator_id,
            created_by_name=operator_name,
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(binding)
        await self.session.flush()
        await self.session.refresh(binding)

        logger.info(
            f"Binding created: id={binding.id}, project_id={project_id}, "
            f"module={module}, sheet_token={lark_sheet_token}"
        )

        return binding

    async def delete_binding(
        self,
        binding_id: uuid.UUID,
    ) -> bool:
        """
        删除飞书表格绑定配置.

        Args:
            binding_id: 绑定配置ID

        Returns:
            bool: 是否删除成功
        """
        result = await self.session.execute(
            select(LarkSheetBinding).where(LarkSheetBinding.id == binding_id)
        )
        binding = result.scalar_one_or_none()

        if not binding:
            logger.warning(f"Binding not found for deletion: {binding_id}")
            return False

        await self.session.delete(binding)
        await self.session.flush()

        logger.info(f"Binding deleted: id={binding_id}")

        return True

    async def toggle_binding_sync(
        self,
        binding_id: uuid.UUID,
        enabled: bool,
    ) -> Optional[LarkSheetBinding]:
        """
        切换绑定配置的同步启用状态.

        Args:
            binding_id: 绑定配置ID
            enabled: 是否启用同步

        Returns:
            Optional[LarkSheetBinding]: 更新后的绑定配置或None
        """
        result = await self.session.execute(
            select(LarkSheetBinding).where(LarkSheetBinding.id == binding_id)
        )
        binding = result.scalar_one_or_none()

        if not binding:
            logger.warning(f"Binding not found for toggle: {binding_id}")
            return None

        binding.sync_enabled = enabled
        binding.status = "active" if enabled else "disabled"
        binding.updated_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(binding)

        logger.info(f"Binding sync toggled: id={binding_id}, enabled={enabled}")

        return binding