"""
PM Digital Employee - Tasks Module
项目经理数字员工系统 - 异步任务模块

包含报告生成、数据同步、知识索引、日常提醒等任务。
"""

from app.tasks.celery_app import celery_app, get_celery_app
from app.tasks.report_tasks import generate_weekly_report, generate_wbs, generate_meeting_minutes
from app.tasks.tasks import (
    sync_lark_sheet_data,
    sync_all_lark_sheets,
    import_excel_data,
    index_knowledge_document,
    reindex_all_knowledge,
    send_daily_reminder,
    send_risk_alert,
    cleanup_expired_cache,
    generate_monthly_statistics,
)


__all__ = [
    "celery_app",
    "get_celery_app",
    # 报告任务
    "generate_weekly_report",
    "generate_wbs",
    "generate_meeting_minutes",
    # 同步任务
    "sync_lark_sheet_data",
    "sync_all_lark_sheets",
    "import_excel_data",
    # RAG任务
    "index_knowledge_document",
    "reindex_all_knowledge",
    # 提醒任务
    "send_daily_reminder",
    "send_risk_alert",
    # 维护任务
    "cleanup_expired_cache",
    "generate_monthly_statistics",
]