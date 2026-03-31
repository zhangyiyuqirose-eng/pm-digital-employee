"""
PM Digital Employee - Pydantic Settings Configuration Module
项目经理数字员工系统 - 配置管理模块

使用Pydantic Settings从环境变量读取配置，支持：
- 类型校验
- 默认值
- 环境变量覆盖
- 嵌套配置
- 验证逻辑

所有敏感配置必须从环境变量读取，禁止硬编码。
"""

from functools import lru_cache
from typing import Literal, Optional
from urllib.parse import quote_plus

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 连接参数
    host: str = Field(default="localhost", description="数据库主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="数据库端口")
    user: str = Field(default="pm_user", description="数据库用户名")
    password: str = Field(default="", description="数据库密码")
    name: str = Field(default="pm_digital_employee", description="数据库名称")

    # 连接池参数
    pool_size: int = Field(default=20, ge=1, le=100, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, le=50, description="连接池溢出数")
    pool_recycle: int = Field(default=3600, ge=60, description="连接回收时间（秒）")
    pool_timeout: float = Field(default=30.0, ge=1.0, description="连接池获取超时（秒）")

    # SSL参数
    ssl_mode: Literal["disable", "prefer", "require", "verify-ca", "verify-full"] = Field(
        default="prefer", description="SSL连接模式"
    )

    # 超时参数
    connect_timeout: float = Field(default=10.0, ge=1.0, description="连接超时（秒）")
    command_timeout: float = Field(default=60.0, ge=1.0, description="命令超时（秒）")

    @property
    def async_url(self) -> str:
        """生成异步数据库连接URL（asyncpg驱动）."""
        password_encoded = quote_plus(self.password)
        return f"postgresql+asyncpg://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """生成同步数据库连接URL（psycopg2驱动）."""
        password_encoded = quote_plus(self.password)
        return f"postgresql://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis缓存配置."""

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Redis主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis端口")
    password: str = Field(default="", description="Redis密码")
    db: int = Field(default=0, ge=0, le=15, description="Redis数据库索引")

    pool_size: int = Field(default=10, ge=1, le=50, description="连接池大小")
    default_ttl: int = Field(default=3600, ge=1, description="默认过期时间（秒）")

    # 超时参数
    connect_timeout: float = Field(default=5.0, ge=0.1, description="连接超时（秒）")
    read_timeout: float = Field(default=5.0, ge=0.1, description="读取超时（秒）")
    write_timeout: float = Field(default=5.0, ge=0.1, description="写入超时（秒）")

    @property
    def url(self) -> str:
        """生成Redis连接URL."""
        if self.password:
            password_encoded = quote_plus(self.password)
            return f"redis://:{password_encoded}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class RabbitMQSettings(BaseSettings):
    """RabbitMQ消息队列配置."""

    model_config = SettingsConfigDict(
        env_prefix="RABBITMQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    user: str = Field(default="pm_rabbitmq", description="RabbitMQ用户名")
    password: str = Field(default="", description="RabbitMQ密码")
    vhost: str = Field(default="pm_vhost", description="RabbitMQ虚拟主机")
    host: str = Field(default="localhost", description="RabbitMQ主机地址")
    port: int = Field(default=5672, ge=1, le=65535, description="RabbitMQ端口")
    mgmt_port: int = Field(default=15672, ge=1, le=65535, description="RabbitMQ管理端口")

    # 连接参数
    heartbeat: int = Field(default=60, ge=10, description="心跳间隔（秒）")
    connection_timeout: float = Field(default=30.0, ge=1.0, description="连接超时（秒）")

    # 消费参数
    prefetch_count: int = Field(default=10, ge=1, description="预取消息数")

    @property
    def url(self) -> str:
        """生成RabbitMQ连接URL."""
        password_encoded = quote_plus(self.password)
        return f"pyamqp://{self.user}:{password_encoded}@{self.host}:{self.port}/{self.vhost}"


class CelerySettings(BaseSettings):
    """Celery异步任务配置."""

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    worker_concurrency: int = Field(default=4, ge=1, le=20, description="Worker并发数")
    task_time_limit: int = Field(default=3600, ge=60, description="任务硬超时（秒）")
    task_soft_time_limit: int = Field(default=3300, ge=30, description="任务软超时（秒）")
    beat_max_interval: int = Field(default=60, ge=10, description="Beat调度间隔（秒）")

    # 任务参数
    max_tasks_per_child: int = Field(default=100, ge=1, description="每个Worker子进程最大任务数")
    acks_late: bool = Field(default=True, description="任务完成后确认")
    task_reject_on_worker_lost: bool = Field(default=True, description="Worker丢失时拒绝任务")


class LarkSettings(BaseSettings):
    """飞书开放平台配置."""

    model_config = SettingsConfigDict(
        env_prefix="LARK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_id: str = Field(default="", description="飞书应用ID")
    app_secret: str = Field(default="", description="飞书应用密钥")
    encrypt_key: str = Field(default="", description="飞书事件加密密钥")
    verification_token: str = Field(default="", description="飞书事件验证Token")

    api_domain: str = Field(default="https://open.feishu.cn", description="飞书API域名")
    token_cache_ttl: int = Field(default=7140, ge=60, description="Token缓存时间（秒）")
    request_timeout: float = Field(default=30.0, ge=1.0, description="请求超时（秒）")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")

    @model_validator(mode="after")
    def validate_app_credentials(self) -> "LarkSettings":
        """验证飞书应用凭证."""
        if self.app_id and not self.app_secret:
            raise ValueError("飞书应用ID存在时，App Secret必须配置")
        return self


class LLMSettings(BaseSettings):
    """大模型配置."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["mock", "openai", "anthropic", "azure", "private"] = Field(
        default="mock", description="LLM提供商"
    )
    model_name: str = Field(default="gpt-4", description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    api_base: str = Field(default="https://api.openai.com/v1", description="API基础URL")

    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, ge=1, description="最大Token数")
    request_timeout: float = Field(default=60.0, ge=1.0, description="请求超时（秒）")
    max_retries: int = Field(default=3, ge=1, le=10, description="最大重试次数")

    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding模型名称")
    embedding_dimension: int = Field(default=1536, ge=256, description="Embedding维度")

    @model_validator(mode="after")
    def validate_api_key(self) -> "LLMSettings":
        """验证API密钥."""
        if self.provider != "mock" and not self.api_key:
            raise ValueError(f"LLM提供商为 {self.provider} 时，API Key必须配置")
        return self


class SecuritySettings(BaseSettings):
    """安全配置."""

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enable_input_validation: bool = Field(default=True, description="启用输入验证")
    enable_prompt_injection_guard: bool = Field(default=True, description="启用提示词注入防护")
    enable_data_masking: bool = Field(default=True, description="启用数据脱敏")
    enable_content_compliance: bool = Field(default=True, description="启用内容合规检查")
    enable_project_isolation: bool = Field(default=True, description="启用项目隔离")

    max_input_length: int = Field(default=10000, ge=100, description="最大输入长度")
    sensitive_words_file: Optional[str] = Field(default=None, description="敏感词文件路径")

    # JWT配置
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1, description="访问令牌过期时间")
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, description="刷新令牌过期时间")


class RAGSettings(BaseSettings):
    """RAG检索配置."""

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    chunk_size: int = Field(default=512, ge=100, le=2000, description="文档切片大小")
    chunk_overlap: int = Field(default=50, ge=0, le=200, description="切片重叠大小")
    top_k: int = Field(default=5, ge=1, le=20, description="检索Top-K数量")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")

    enable_rerank: bool = Field(default=True, description="启用检索重排")
    rerank_model: str = Field(default="cross-encoder", description="重排模型名称")


class AuditSettings(BaseSettings):
    """审计日志配置."""

    model_config = SettingsConfigDict(
        env_prefix="AUDIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enable: bool = Field(default=True, description="启用审计日志")
    log_path: str = Field(default="/var/log/pm_digital_employee/audit", description="审计日志路径")
    retention_days: int = Field(default=180, ge=30, description="日志保留天数")
    enable_encryption: bool = Field(default=True, description="启用加密存储")


class LogSettings(BaseSettings):
    """日志配置."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="日志级别"
    )
    format: Literal["json", "text"] = Field(default="json", description="日志格式")
    file_path: str = Field(default="/var/log/pm_digital_employee", description="日志文件路径")
    max_size: int = Field(default=100, ge=10, description="日志文件最大大小（MB）")
    max_files: int = Field(default=10, ge=1, description="日志文件最大数量")
    enable_compression: bool = Field(default=True, description="启用日志压缩")


class MetricsSettings(BaseSettings):
    """监控指标配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS", description="启用Prometheus指标")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, alias="METRICS_PORT", description="指标端口")
    enable_health_details: bool = Field(
        default=True, alias="ENABLE_HEALTH_DETAILS", description="启用健康检查详细指标"
    )


class SessionSettings(BaseSettings):
    """会话与上下文配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    context_ttl: int = Field(default=28800, ge=60, alias="SESSION_CONTEXT_TTL", description="上下文缓存时间")
    dialog_state_ttl: int = Field(default=1800, ge=60, alias="DIALOG_STATE_TTL", description="对话状态过期时间")
    max_dialog_rounds: int = Field(default=5, ge=1, alias="MAX_DIALOG_ROUNDS", description="最大对话轮数")


class PermissionSettings(BaseSettings):
    """权限配置."""

    model_config = SettingsConfigDict(
        env_prefix="PERMISSION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cache_ttl: int = Field(default=3600, ge=60, description="权限缓存时间（秒）")
    group_binding_cache_ttl: int = Field(default=86400, ge=60, description="群绑定缓存时间（秒）")
    default_deny: bool = Field(default=True, description="默认拒绝策略")


class ScheduleSettings(BaseSettings):
    """定时任务配置."""

    model_config = SettingsConfigDict(
        env_prefix="SCHEDULE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enable_progress_check: bool = Field(default=True, description="启用每日进度检查")
    progress_check_cron: str = Field(default="0 9 * * *", description="进度检查时间")
    enable_risk_scan: bool = Field(default=True, description="启用每日风险扫描")
    risk_scan_cron: str = Field(default="*/30 * * * *", description="风险扫描时间")
    enable_weekly_report: bool = Field(default=True, description="启用周报自动生成")
    weekly_report_cron: str = Field(default="0 17 * * 5", description="周报生成时间")


class AppSettings(BaseSettings):
    """应用主配置."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="PM Digital Employee", description="应用名称")
    env: Literal["development", "testing", "production"] = Field(
        default="development", description="运行环境"
    )
    debug: bool = Field(default=False, description="调试模式")
    secret_key: str = Field(
        default="change_this_to_secure_secret_key_in_production",
        min_length=32,
        description="应用密钥",
    )
    host: str = Field(default="0.0.0.0", description="主机绑定地址")
    port: int = Field(default=8000, ge=1024, le=65535, description="应用端口")
    workers: int = Field(default=4, ge=1, le=20, description="工作进程数")
    version: str = Field(default="v1", description="API版本号")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """验证应用密钥安全性."""
        if v == "change_this_to_secure_secret_key_in_production":
            # 开发环境允许默认值，生产环境必须使用真实密钥
            env_val = info.data.get("env", "development")
            if env_val == "production":
                raise ValueError("生产环境必须配置安全的APP_SECRET_KEY")
        return v

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """验证调试模式."""
        env_val = info.data.get("env", "development")
        if v and env_val == "production":
            raise ValueError("生产环境必须关闭调试模式")
        return v


class Settings(BaseSettings):
    """全局配置汇总."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 子配置
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    lark: LarkSettings = Field(default_factory=LarkSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    audit: AuditSettings = Field(default_factory=AuditSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    metrics: MetricsSettings = Field(default_factory=MetricsSettings)
    session: SessionSettings = Field(default_factory=SessionSettings)
    permission: PermissionSettings = Field(default_factory=PermissionSettings)
    schedule: ScheduleSettings = Field(default_factory=ScheduleSettings)

    @property
    def is_production(self) -> bool:
        """是否为生产环境."""
        return self.app.env == "production"

    @property
    def is_development(self) -> bool:
        """是否为开发环境."""
        return self.app.env == "development"

    @property
    def is_testing(self) -> bool:
        """是否为测试环境."""
        return self.app.env == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    获取全局配置实例（缓存）.

    使用lru_cache确保配置只加载一次，
    避免重复解析环境变量。

    Returns:
        Settings: 全局配置实例
    """
    return Settings()


# 配置实例导出
settings: Settings = get_settings()