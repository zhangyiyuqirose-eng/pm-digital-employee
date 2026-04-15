"""
PM Digital Employee - Configuration
PM Digital Employee System - Configuration Management

Lark as the primary user interaction entrypoint.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = "PM Digital Employee"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "dev_secret_key"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./pm_digital_employee.db"

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Lark configuration
    lark_app_id: str = ""
    lark_app_secret: str = ""
    lark_encrypt_key: str = ""  # Event encrypt key
    lark_verification_token: str = ""  # Callback verification token
    lark_api_domain: str = "https://open.feishu.cn"
    lark_tenant_token_ttl: int = 7200

    # LLM settings
    llm_provider: str = "mock"
    llm_model_name: str = "gpt-4"
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # Security settings
    security_enable_input_validation: bool = True
    security_max_input_length: int = 10000

    # Celery settings
    celery_broker_url: str = "pyamqp://guest@localhost//"
    celery_result_backend: str = "redis://localhost:6379/1"

    @property
    def lark_configured(self) -> bool:
        """Check if Lark is configured."""
        return bool(self.lark_app_id and self.lark_app_secret)


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（单例）."""
    return Settings()


# 全局配置实例
settings = get_settings()