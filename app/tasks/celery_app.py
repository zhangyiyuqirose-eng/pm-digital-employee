"""
PM Digital Employee - Celery App Configuration
项目经理数字员工系统 - Celery异步任务配置
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "pm_digital_employee",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "app.tasks.report_tasks",
        "app.tasks.event_tasks",
    ],
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=86400,  # 结果保存24小时
    task_routes={
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.event_tasks.*": {"queue": "events"},
    },
    beat_schedule={
        "weekly-report-reminder": {
            "task": "app.tasks.scheduled_tasks.weekly_report_reminder",
            "schedule": 60 * 60 * 24 * 7,  # 每周
        },
        "risk-monitor": {
            "task": "app.tasks.scheduled_tasks.risk_monitor_check",
            "schedule": 60 * 60,  # 每小时
        },
    },
)


def get_celery_app() -> Celery:
    """获取Celery应用实例."""
    return celery_app