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


class LLMSettings(BaseSettings):
    """LLM configuration."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    # Provider settings
    provider: str = "openai"
    model_name: str = "MiniMax-M2.5"
    api_key: str = ""
    api_base: str = "https://www.finna.com.cn/v1"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    retry_count: int = 3
    retry_delay: float = 1.0

    # Intent recognition settings
    intent_model: str = "MiniMax-M2.5"
    intent_max_tokens: int = 1000
    intent_temperature: float = 0.3

    # OpenAI settings (兼容 Finna API)
    openai_api_key: str = ""
    openai_api_base: str = "https://www.finna.com.cn/v1"
    openai_model: str = "MiniMax-M2.5"

    # Azure OpenAI settings
    azure_api_key: str = ""
    azure_api_base: str = ""
    azure_api_version: str = "2024-02-01"
    azure_deployment: str = "gpt-4"

    # Zhipu (智谱) settings
    zhipu_api_key: str = ""
    zhipu_model: str = "glm-4"

    # Qwen (通义千问) settings
    qwen_api_key: str = ""
    qwen_model: str = "qwen-max"


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    url: str = "sqlite+aiosqlite:///./pm_digital_employee.db"
    async_url: str = "sqlite+aiosqlite:///./pm_digital_employee.db"
    host: str = "localhost"
    port: int = 5432
    name: str = "pm_digital_employee"
    user: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    pool_timeout: int = 30


class RedisSettings(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    url: str = "redis://localhost:6379/0"
    host: str = "redis"  # Docker网络中的服务名
    port: int = 6379
    db: int = 0
    password: str = "redis_123"  # 默认密码
    pool_size: int = 10

    def get_connection_url(self) -> str:
        """构建Redis连接URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


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

    @property
    def is_development(self) -> bool:
        """是否为开发环境."""
        return self.app_env == "development"

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./pm_digital_employee.db"

    # Nested Database settings (for compatibility)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"

    # Nested Redis settings (for compatibility)
    redis: RedisSettings = Field(default_factory=RedisSettings)

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

    # Nested LLM settings (for compatibility)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    # Security settings
    security_enable_input_validation: bool = True
    security_max_input_length: int = 10000

    # CORS settings
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_origin_regex: Optional[str] = None

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