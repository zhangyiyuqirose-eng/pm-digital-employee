"""
PM Digital Employee - Lark Sheet Webhook Handler
项目经理数字员工系统 - 飞书在线表格Webhook处理器

实现飞书表格Webhook接收、实时双向同步触发器、
同步频率配置、失败重试机制和同步状态监控。

v1.2.0新增
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.integrations.lark.client import LarkClient, get_lark_client
from app.integrations.lark.signature import verify_lark_signature

logger = get_logger(__name__)


# ==================== 同步频率配置 ====================

class SyncFrequency:
    """同步频率配置."""

    REALTIME = "realtime"      # 实时同步（Webhook触发）
    FIVE_MIN = "5min"          # 5分钟定时同步
    FIFTEEN_MIN = "15min"      # 15分钟定时同步
    ONE_HOUR = "1hour"         # 1小时定时同步

    # 频率映射到Celery任务间隔
    FREQUENCY_INTERVALS = {
        REALTIME: None,        # 实时由Webhook触发，无定时任务
        FIVE_MIN: 5 * 60,      # 5分钟 = 300秒
        FIFTEEN_MIN: 15 * 60,  # 15分钟 = 900秒
        ONE_HOUR: 60 * 60,     # 1小时 = 3600秒
    }

    @staticmethod
    def get_interval_seconds(frequency: str) -> Optional[int]:
        """获取频率对应的间隔秒数."""
        return SyncFrequency.FREQUENCY_INTERVALS.get(frequency)


# ==================== 同步状态 ====================

class SyncStatus:
    """同步状态."""

    PENDING = "pending"        # 待同步
    RUNNING = "running"        # 同步中
    SUCCESS = "success"        # 同步成功
    FAILED = "failed"          # 同步失败
    PARTIAL = "partial"        # 部分成功
    RETRYING = "retrying"      # 重试中


# ==================== Webhook事件处理器 ====================

class LarkSheetWebhookHandler:
    """
    飞书在线表格Webhook处理器.

    处理飞书表格变更事件，触发实时双向同步。
    """

    def __init__(self, client: Optional[LarkClient] = None) -> None:
        """
        初始化Webhook处理器.

        Args:
            client: Lark客户端实例
        """
        self._client = client or get_lark_client()
        self._sync_handlers: Dict[str, Callable] = {}

    def register_sync_handler(self, module: str, handler: Callable) -> None:
        """
        注册模块同步处理器.

        Args:
            module: 功能模块名称
            handler: 同步处理函数
        """
        self._sync_handlers[module] = handler
        logger.info(f"Registered sync handler for module: {module}")

    async def handle_webhook_event(
        self,
        event_data: Dict[str, Any],
        binding_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        处理飞书表格Webhook事件.

        Args:
            event_data: Webhook事件数据
            binding_config: 表格绑定配置

        Returns:
            Dict: 处理结果
        """
        event_type = event_data.get("type", "")
        logger.info(f"Processing Webhook event: {event_type}")

        # 判断事件类型
        if event_type == "sheet_data_change":
            return await self._handle_data_change(event_data, binding_config)
        elif event_type == "sheet_structure_change":
            return await self._handle_structure_change(event_data, binding_config)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"status": "ignored", "reason": "unknown_event_type"}

    async def _handle_data_change(
        self,
        event_data: Dict[str, Any],
        binding_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        处理数据变更事件.

        Args:
            event_data: 事件数据
            binding_config: 绑定配置

        Returns:
            Dict: 处理结果
        """
        module = binding_config.get("module", "")
        sync_mode = binding_config.get("sync_mode", "bidirectional")

        # 检查是否启用实时同步
        if binding_config.get("sync_frequency") != SyncFrequency.REALTIME:
            logger.info(f"Binding {binding_config.get('id')} not realtime, skip webhook")
            return {"status": "skipped", "reason": "not_realtime_mode"}

        # 检查同步方向
        if sync_mode == "to_sheet":
            # 只同步到飞书表格，忽略飞书表格变更
            return {"status": "skipped", "reason": "sync_to_sheet_only"}

        # 获取变更范围
        changes = event_data.get("changes", [])
        if not changes:
            return {"status": "success", "records_synced": 0}

        # 触发同步处理器
        handler = self._sync_handlers.get(module)
        if not handler:
            logger.warning(f"No handler registered for module: {module}")
            return {"status": "failed", "reason": "no_handler"}

        # 执行同步
        try:
            result = await handler(
                binding_id=binding_config.get("id"),
                changes=changes,
                direction="from_sheet",
            )
            return result
        except Exception as e:
            logger.error(f"Sync handler failed: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    async def _handle_structure_change(
        self,
        event_data: Dict[str, Any],
        binding_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        处理表格结构变更事件.

        Args:
            event_data: 事件数据
            binding_config: 绑定配置

        Returns:
            Dict: 处理结果
        """
        # 结构变更需要重新校验字段映射
        logger.warning(
            f"Sheet structure changed for binding {binding_config.get('id')}, "
            "field mappings may need update"
        )
        return {
            "status": "warning",
            "reason": "structure_changed",
            "message": "请检查字段映射配置是否需要更新",
        }


# ==================== 同步触发器 ====================

class LarkSheetSyncTrigger:
    """
    飞书表格同步触发器.

    管理双向同步触发逻辑，包括实时触发和定时触发。
    """

    def __init__(
        self,
        webhook_handler: Optional[LarkSheetWebhookHandler] = None,
    ) -> None:
        """
        初始化同步触发器.

        Args:
            webhook_handler: Webhook处理器实例
        """
        self._webhook_handler = webhook_handler or LarkSheetWebhookHandler()
        self._pending_syncs: Dict[str, Dict] = {}  # 待同步任务队列

    async def trigger_realtime_sync(
        self,
        binding_id: str,
        direction: str,
        changes: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        触发实时同步.

        Args:
            binding_id: 绑定配置ID
            direction: 同步方向（to_sheet/from_sheet）
            changes: 变更数据（可选）

        Returns:
            Dict: 同步结果
        """
        logger.info(f"Triggering realtime sync for binding {binding_id}, direction={direction}")

        # 创建同步任务
        sync_task = {
            "binding_id": binding_id,
            "direction": direction,
            "changes": changes or [],
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "trigger_type": "realtime",
        }

        # 执行同步（通过注册的处理器）
        # 实际同步逻辑由各模块的handler实现
        return {
            "status": SyncStatus.PENDING,
            "task_id": str(uuid.uuid4()),
            "triggered_at": sync_task["triggered_at"],
        }

    async def trigger_scheduled_sync(
        self,
        binding_id: str,
        frequency: str,
    ) -> Dict[str, Any]:
        """
        触发定时同步.

        Args:
            binding_id: 绑定配置ID
            frequency: 同步频率

        Returns:
            Dict: 同步任务信息
        """
        logger.info(f"Triggering scheduled sync for binding {binding_id}, frequency={frequency}")

        # 定时同步任务信息
        sync_task = {
            "binding_id": binding_id,
            "frequency": frequency,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "trigger_type": "scheduled",
        }

        return {
            "status": SyncStatus.PENDING,
            "task_id": str(uuid.uuid4()),
            "triggered_at": sync_task["triggered_at"],
        }

    async def trigger_manual_sync(
        self,
        binding_id: str,
        direction: str = "bidirectional",
    ) -> Dict[str, Any]:
        """
        触发手动同步.

        Args:
            binding_id: 绑定配置ID
            direction: 同步方向

        Returns:
            Dict: 同步任务信息
        """
        logger.info(f"Triggering manual sync for binding {binding_id}")

        return {
            "status": SyncStatus.PENDING,
            "task_id": str(uuid.uuid4()),
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "trigger_type": "manual",
            "direction": direction,
        }


# ==================== 失败重试机制 ====================

class SyncRetryManager:
    """
    同步失败重试管理器.

    实现失败重试策略：最多3次重试，间隔递增。
    """

    MAX_RETRIES = 3
    RETRY_DELAYS = [30, 60, 120]  # 重试间隔：30秒、60秒、120秒

    def __init__(self) -> None:
        """初始化重试管理器."""
        self._retry_queue: Dict[str, Dict] = {}

    def should_retry(self, sync_log: Dict[str, Any]) -> bool:
        """
        判断是否需要重试.

        Args:
            sync_log: 同步日志

        Returns:
            bool: 是否需要重试
        """
        retry_count = sync_log.get("retry_count", 0)
        if retry_count >= self.MAX_RETRIES:
            return False

        # 非失败状态不重试
        if sync_log.get("status") != SyncStatus.FAILED:
            return False

        return True

    def get_retry_delay(self, retry_count: int) -> int:
        """
        获取重试延迟时间（秒）.

        Args:
            retry_count: 当前重试次数

        Returns:
            int: 延迟秒数
        """
        if retry_count >= len(self.RETRY_DELAYS):
            return self.RETRY_DELAYS[-1]
        return self.RETRY_DELAYS[retry_count]

    def schedule_retry(
        self,
        sync_log_id: str,
        binding_id: str,
        retry_count: int,
    ) -> Dict[str, Any]:
        """
        安排重试任务.

        Args:
            sync_log_id: 同步日志ID
            binding_id: 绑定配置ID
            retry_count: 当前重试次数

        Returns:
            Dict: 重试任务信息
        """
        delay = self.get_retry_delay(retry_count)
        retry_at = datetime.now(timezone.utc).timestamp() + delay

        retry_task = {
            "sync_log_id": sync_log_id,
            "binding_id": binding_id,
            "retry_count": retry_count + 1,
            "retry_at": retry_at,
            "delay_seconds": delay,
        }

        self._retry_queue[sync_log_id] = retry_task
        logger.info(
            f"Scheduled retry for sync log {sync_log_id}, "
            f"retry #{retry_count + 1} after {delay}s"
        )

        return retry_task

    def get_pending_retries(self) -> List[Dict[str, Any]]:
        """
        获取待执行的重试任务.

        Returns:
            List: 待重试任务列表
        """
        now = datetime.now(timezone.utc).timestamp()
        pending = []

        for sync_log_id, task in self._retry_queue.items():
            if task["retry_at"] <= now:
                pending.append(task)
                del self._retry_queue[sync_log_id]

        return pending

    def clear_retry(self, sync_log_id: str) -> None:
        """
        清除重试任务.

        Args:
            sync_log_id: 同步日志ID
        """
        if sync_log_id in self._retry_queue:
            del self._retry_queue[sync_log_id]


# ==================== 同步状态监控 ====================

class SyncStatusMonitor:
    """
    同步状态监控器.

    提供同步状态查询和健康检查功能。
    """

    def __init__(self) -> None:
        """初始化状态监控器."""
        self._status_cache: Dict[str, Dict] = {}

    def update_status(
        self,
        binding_id: str,
        status: str,
        details: Optional[Dict] = None,
    ) -> None:
        """
        更新同步状态.

        Args:
            binding_id: 绑定配置ID
            status: 同步状态
            details: 详细信息
        """
        self._status_cache[binding_id] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

    def get_status(self, binding_id: str) -> Optional[Dict[str, Any]]:
        """
        获取同步状态.

        Args:
            binding_id: 绑定配置ID

        Returns:
            Dict: 状态信息
        """
        return self._status_cache.get(binding_id)

    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有绑定配置的同步状态.

        Returns:
            Dict: 所有状态信息
        """
        return self._status_cache.copy()

    def check_health(self, binding_id: str) -> Dict[str, Any]:
        """
        检查绑定配置的健康状态.

        Args:
            binding_id: 绑定配置ID

        Returns:
            Dict: 健康检查结果
        """
        status_info = self._status_cache.get(binding_id)

        if not status_info:
            return {
                "healthy": False,
                "reason": "no_status_record",
                "message": "未找到同步状态记录",
            }

        status = status_info.get("status")
        updated_at = status_info.get("updated_at")

        # 检查状态
        if status == SyncStatus.FAILED:
            return {
                "healthy": False,
                "reason": "last_sync_failed",
                "message": "最近一次同步失败",
                "details": status_info.get("details"),
            }

        # 检查是否长时间未同步
        if updated_at:
            updated_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            hours_since_sync = (datetime.now(timezone.utc) - updated_time).total_seconds() / 3600

            if hours_since_sync > 2:
                return {
                    "healthy": False,
                    "reason": "sync_stale",
                    "message": f"超过{hours_since_sync:.1f}小时未同步",
                }

        return {
            "healthy": True,
            "last_sync_at": updated_at,
            "last_sync_status": status,
        }


# ==================== 全局实例 ====================

_webhook_handler: Optional[LarkSheetWebhookHandler] = None
_sync_trigger: Optional[LarkSheetSyncTrigger] = None
_retry_manager: Optional[SyncRetryManager] = None
_status_monitor: Optional[SyncStatusMonitor] = None


def get_webhook_handler() -> LarkSheetWebhookHandler:
    """获取Webhook处理器实例."""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = LarkSheetWebhookHandler()
    return _webhook_handler


def get_sync_trigger() -> LarkSheetSyncTrigger:
    """获取同步触发器实例."""
    global _sync_trigger
    if _sync_trigger is None:
        _sync_trigger = LarkSheetSyncTrigger()
    return _sync_trigger


def get_retry_manager() -> SyncRetryManager:
    """获取重试管理器实例."""
    global _retry_manager
    if _retry_manager is None:
        _retry_manager = SyncRetryManager()
    return _retry_manager


def get_status_monitor() -> SyncStatusMonitor:
    """获取状态监控器实例."""
    global _status_monitor
    if _status_monitor is None:
        _status_monitor = SyncStatusMonitor()
    return _status_monitor