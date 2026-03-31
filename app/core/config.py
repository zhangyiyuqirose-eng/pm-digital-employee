"""
PM Digital Employee - Configuration
项目经理数字员工系统 - 配置管理
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用配置
    app_name: str = "PM Digital Employee"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "dev_secret_key"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./pm_digital_employee.db"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # 飞书配置
    lark_app_id: str = ""
    lark_app_secret: str = ""
    lark_encrypt_key: str = ""
    lark_verification_token: str = ""
    lark_api_domain: str = "https://open.feishu.cn"

    # LLM配置
    llm_provider: str = "mock"
    llm_model_name: str = "gpt-4"
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 安全配置
    security_enable_input_validation: bool = True
    security_max_input_length: int = 10000

    # Celery配置
    celery_broker_url: str = "pyamqp://guest@localhost//"
    celery_result_backend: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（单例）."""
    return Settings()


# 全局配置实例
settings = get_settings()