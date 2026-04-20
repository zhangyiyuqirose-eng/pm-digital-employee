"""
PM Digital Employee - Lark Sheet Sync Tasks
项目经理数字员工系统 - 飞书在线表格同步Celery定时任务

实现定时同步任务（5min/15min/1hour）和失败重试任务。

v1.2.0新增
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


# ==================== 定时同步任务 ====================

@celery_app.task(
    name="lark_sheet_sync_5min",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def sync_lark_sheet_5min(self) -> Dict[str, Any]:
    """
    5分钟定时同步任务.

    执行所有sync_frequency=5min的绑定配置同步。

    Returns:
        Dict: 任务执行结果
    """
    logger.info("Starting 5min lark sheet sync task")
    
    try:
        # 导入必要模块（避免循环依赖）
        from app.integrations.lark.sheet_webhook import (
            SyncFrequency,
            get_sync_trigger,
            get_status_monitor,
        )
        
        # 获取所有5分钟同步频率的绑定配置
        # 实际实现需要查询数据库
        bindings = _get_bindings_by_frequency(SyncFrequency.FIVE_MIN)
        
        if not bindings:
            logger.info("No bindings with 5min sync frequency")
            return {"status": "completed", "bindings_processed": 0}
        
        results = []
        for binding in bindings:
            result = _execute_sync(binding)
            results.append(result)
            
            # 更新状态监控
            get_status_monitor().update_status(
                str(binding.get("id")),
                result.get("status"),
                result,
            )
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") == "failed")
        
        logger.info(
            f"5min sync completed: {success_count} success, {failed_count} failed"
        )
        
        return {
            "status": "completed",
            "bindings_processed": len(bindings),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"5min sync task failed: {e}", exc_info=True)
        # 重试
        raise self.retry(exc=e)


@celery_app.task(
    name="lark_sheet_sync_15min",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sync_lark_sheet_15min(self) -> Dict[str, Any]:
    """
    15分钟定时同步任务.

    执行所有sync_frequency=15min的绑定配置同步。

    Returns:
        Dict: 任务执行结果
    """
    logger.info("Starting 15min lark sheet sync task")
    
    try:
        from app.integrations.lark.sheet_webhook import (
            SyncFrequency,
            get_sync_trigger,
            get_status_monitor,
        )
        
        bindings = _get_bindings_by_frequency(SyncFrequency.FIFTEEN_MIN)
        
        if not bindings:
            logger.info("No bindings with 15min sync frequency")
            return {"status": "completed", "bindings_processed": 0}
        
        results = []
        for binding in bindings:
            result = _execute_sync(binding)
            results.append(result)
            
            get_status_monitor().update_status(
                str(binding.get("id")),
                result.get("status"),
                result,
            )
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") == "failed")
        
        logger.info(
            f"15min sync completed: {success_count} success, {failed_count} failed"
        )
        
        return {
            "status": "completed",
            "bindings_processed": len(bindings),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"15min sync task failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    name="lark_sheet_sync_1hour",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def sync_lark_sheet_1hour(self) -> Dict[str, Any]:
    """
    1小时定时同步任务.

    执行所有sync_frequency=1hour的绑定配置同步。

    Returns:
        Dict: 任务执行结果
    """
    logger.info("Starting 1hour lark sheet sync task")
    
    try:
        from app.integrations.lark.sheet_webhook import (
            SyncFrequency,
            get_sync_trigger,
            get_status_monitor,
        )
        
        bindings = _get_bindings_by_frequency(SyncFrequency.ONE_HOUR)
        
        if not bindings:
            logger.info("No bindings with 1hour sync frequency")
            return {"status": "completed", "bindings_processed": 0}
        
        results = []
        for binding in bindings:
            result = _execute_sync(binding)
            results.append(result)
            
            get_status_monitor().update_status(
                str(binding.get("id")),
                result.get("status"),
                result,
            )
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") == "failed")
        
        logger.info(
            f"1hour sync completed: {success_count} success, {failed_count} failed"
        )
        
        return {
            "status": "completed",
            "bindings_processed": len(bindings),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }
        
    except Exception as e:
        logger.error(f"1hour sync task failed: {e}", exc_info=True)
        raise self.retry(exc=e)


# ==================== 失败重试任务 ====================

@celery_app.task(
    name="lark_sheet_sync_retry",
    bind=True,
    max_retries=5,
)
def retry_failed_sync(self, sync_log_id: str, binding_id: str) -> Dict[str, Any]:
    """
    失败同步重试任务.

    对失败的同步任务执行重试。

    Args:
        sync_log_id: 同步日志ID
        binding_id: 绑定配置ID

    Returns:
        Dict: 重试结果
    """
    logger.info(f"Retrying failed sync: sync_log_id={sync_log_id}, binding_id={binding_id}")
    
    try:
        from app.integrations.lark.sheet_webhook import (
            get_retry_manager,
            get_status_monitor,
            SyncStatus,
        )
        
        # 获取绑定配置
        binding = _get_binding_by_id(binding_id)
        if not binding:
            logger.warning(f"Binding {binding_id} not found")
            return {"status": "failed", "reason": "binding_not_found"}
        
        # 执行同步
        result = _execute_sync(binding)
        
        # 更新状态
        get_status_monitor().update_status(binding_id, result.get("status"), result)
        
        # 如果仍然失败，检查是否需要继续重试
        if result.get("status") == SyncStatus.FAILED:
            sync_log = {
                "id": sync_log_id,
                "status": SyncStatus.FAILED,
                "retry_count": self.request.retries,
            }
            
            if get_retry_manager().should_retry(sync_log):
                # 安排下一次重试
                retry_task = get_retry_manager().schedule_retry(
                    sync_log_id,
                    binding_id,
                    self.request.retries,
                )
                
                # 触发延迟重试任务
                retry_failed_sync.apply_async(
                    args=[sync_log_id, binding_id],
                    countdown=retry_task["delay_seconds"],
                )
                
                logger.info(f"Scheduled retry #{self.request.retries + 1} for {sync_log_id}")
                return {"status": "retrying", "next_retry_in": retry_task["delay_seconds"]}
            else:
                logger.warning(f"Max retries reached for {sync_log_id}")
                return {"status": "failed", "reason": "max_retries_reached"}
        
        # 成功则清除重试队列
        get_retry_manager().clear_retry(sync_log_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Retry task failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(name="lark_sheet_sync_check_retries")
def check_pending_retries() -> Dict[str, Any]:
    """
    检查待执行的重试任务.

    定期扫描重试队列，触发到期重试。

    Returns:
        Dict: 检查结果
    """
    logger.info("Checking pending retry tasks")
    
    try:
        from app.integrations.lark.sheet_webhook import get_retry_manager
        
        pending = get_retry_manager().get_pending_retries()
        
        if not pending:
            logger.info("No pending retries")
            return {"status": "completed", "retries_triggered": 0}
        
        # 触发重试任务
        for task in pending:
            retry_failed_sync.apply_async(
                args=[task["sync_log_id"], task["binding_id"]],
            )
            logger.info(f"Triggered retry for sync_log_id={task['sync_log_id']}")
        
        return {
            "status": "completed",
            "retries_triggered": len(pending),
        }
        
    except Exception as e:
        logger.error(f"Check retries task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


# ==================== 手动同步任务 ====================

@celery_app.task(
    name="lark_sheet_sync_manual",
    bind=True,
    max_retries=2,
)
def manual_sync_binding(self, binding_id: str, direction: str = "bidirectional") -> Dict[str, Any]:
    """
    手动同步任务.

    执行指定绑定配置的手动同步。

    Args:
        binding_id: 绑定配置ID
        direction: 同步方向

    Returns:
        Dict: 同步结果
    """
    logger.info(f"Manual sync: binding_id={binding_id}, direction={direction}")
    
    try:
        from app.integrations.lark.sheet_webhook import get_status_monitor
        
        binding = _get_binding_by_id(binding_id)
        if not binding:
            return {"status": "failed", "reason": "binding_not_found"}
        
        # 执行同步
        result = _execute_sync(binding, direction)
        
        # 更新状态
        get_status_monitor().update_status(binding_id, result.get("status"), result)
        
        return result
        
    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        raise self.retry(exc=e)


# ==================== 辅助函数 ====================

def _get_bindings_by_frequency(frequency: str) -> list:
    """
    根据同步频率获取绑定配置列表.

    Args:
        frequency: 同步频率

    Returns:
        list: 绑定配置列表
    """
    # TODO: 实现数据库查询
    # 示例查询逻辑：
    # from app.repositories.lark_sheet_binding_repo import get_binding_repo
    # repo = get_binding_repo()
    # return repo.get_by_frequency(frequency, enabled_only=True)
    
    # 暂返回空列表（实际需要连接数据库）
    logger.debug(f"Querying bindings with frequency={frequency}")
    return []


def _get_binding_by_id(binding_id: str) -> Optional[Dict[str, Any]]:
    """
    根据ID获取绑定配置.

    Args:
        binding_id: 绑定配置ID

    Returns:
        Dict: 绑定配置
    """
    # TODO: 实现数据库查询
    # from app.repositories.lark_sheet_binding_repo import get_binding_repo
    # repo = get_binding_repo()
    # return repo.get_by_id(binding_id)
    
    logger.debug(f"Querying binding by id={binding_id}")
    return None


def _execute_sync(
    binding: Dict[str, Any],
    direction: str = "bidirectional",
) -> Dict[str, Any]:
    """
    执行同步操作.

    Args:
        binding: 绑定配置
        direction: 同步方向

    Returns:
        Dict: 同步结果
    """
    # TODO: 实现实际同步逻辑
    # 需要根据module调用对应的同步处理器
    
    binding_id = str(binding.get("id"))
    module = binding.get("module")
    
    logger.info(f"Executing sync for binding {binding_id}, module={module}")
    
    # 模拟同步结果
    return {
        "status": "success",
        "binding_id": binding_id,
        "module": module,
        "records_synced": 0,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== Celery Beat配置 ====================

# 定时任务调度配置（需要在celery_app.py中注册）
CELERY_BEAT_SCHEDULE = {
    # 5分钟同步任务
    "lark-sheet-sync-5min": {
        "task": "lark_sheet_sync_5min",
        "schedule": 300.0,  # 每5分钟
    },
    # 15分钟同步任务
    "lark-sheet-sync-15min": {
        "task": "lark_sheet_sync_15min",
        "schedule": 900.0,  # 每15分钟
    },
    # 1小时同步任务
    "lark-sheet-sync-1hour": {
        "task": "lark_sheet_sync_1hour",
        "schedule": 3600.0,  # 每1小时
    },
    # 重试检查任务（每分钟检查）
    "lark-sheet-sync-check-retries": {
        "task": "lark_sheet_sync_check_retries",
        "schedule": 60.0,  # 每1分钟
    },
}