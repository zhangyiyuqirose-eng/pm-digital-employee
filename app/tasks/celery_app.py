"""
PM Digital Employee - Celery App Configuration
项目经理数字员工系统 - Celery异步任务配置
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "pm_digital_employee",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.report_tasks",
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
)


def get_celery_app() -> Celery:
    """获取Celery应用实例."""
    return celery_app