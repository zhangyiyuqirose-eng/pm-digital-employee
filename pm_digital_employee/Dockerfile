# PM Digital Employee - Production Dockerfile
# 国有大型银行科技子公司项目管理部 - 项目经理数字员工系统
# 多阶段构建，优化镜像大小和安全性

# ============================================
# Stage 1: Builder - 构建Python环境和依赖
# ============================================
FROM python:3.11-slim-bookworm AS builder

# 设置构建参数
ARG PYTHON_VERSION=3.11
ARG PIP_TIMEOUT=120

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=${PIP_TIMEOUT} \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_INSTALLER_MAX_WORKERS=10

# 安装系统构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    cmake \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml ./

# 安装Poetry和项目依赖
RUN pip install --upgrade pip setuptools wheel \
    && pip install poetry==2.0.0 \
    && poetry install --only main --no-interaction --no-ansi \
    && pip uninstall -y poetry \
    && rm -rf ~/.cache/pypoetry ~/.cache/pip

# ============================================
# Stage 2: Development - 开发环境镜像
# ============================================
FROM python:3.11-slim-bookworm AS development

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app \
    APP_ENV=development \
    APP_DEBUG=true

# 安装系统运行依赖（包含开发工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libssl3 \
    libffi8 \
    libjpeg62-turbo \
    zlib1g \
    curl \
    vim \
    procps \
    net-tools \
    htop \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建应用目录和非root用户
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 从builder复制已安装的包
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建必要目录并设置权限
RUN mkdir -p /var/log/pm_digital_employee /app/data \
    && chown -R appuser:appuser /app /var/log/pm_digital_employee

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 开发环境启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 3: Production - 生产环境镜像
# ============================================
FROM python:3.11-slim-bookworm AS production

# 设置构建参数
ARG PYTHON_VERSION=3.11
ARG APP_VERSION=1.0.0

# 设置生产环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app \
    APP_ENV=production \
    APP_DEBUG=false \
    APP_VERSION=${APP_VERSION} \
    # 安全配置
    PYTHONHASHSEED=random \
    # 性能配置
    UVICORN_WORKERS=4 \
    UVICORN_LIMIT_CONCURRENCY=100 \
    UVICORN_BACKLOG=2048

# 安装系统运行依赖（最小化）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libssl3 \
    libffi8 \
    libjpeg62-turbo \
    zlib1g \
    curl \
    # 安全工具
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    # 安全清理
    && rm -rf /tmp/* /var/tmp/* /root/.cache

# 创建应用目录和专用用户（不使用root）
WORKDIR /app
RUN groupadd -r appgroup \
    && useradd -r -g appgroup -d /app -s /sbin/nologin -c "PM Digital Employee" appuser \
    && chmod 755 /app

# 从builder复制已安装的包
COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码（按顺序，优先复制不变的文件）
COPY --chown=appuser:appgroup pyproject.toml ./
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup prompts ./prompts
COPY --chown=appuser:appgroup scripts ./scripts

# 创建必要目录并设置权限
RUN mkdir -p /var/log/pm_digital_employee /app/data \
    && chown -R appuser:appgroup /app /var/log/pm_digital_employee \
    && chmod -R 755 /app \
    && chmod 750 /var/log/pm_digital_employee

# 安全配置：移除不必要的文件
RUN find /app -type f -name "*.pyc" -delete \
    && find /app -type f -name "*.pyo" -delete \
    && find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app -type f -name "*.log" -delete \
    && find /app -type f -name ".git*" -delete

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000 9090

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 使用dumb-init作为入口点，正确处理信号
ENTRYPOINT ["dumb-init", "--", "uvicorn", "app.main:app"]

# 默认启动参数（可被docker-compose覆盖）
CMD ["--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]

# ============================================
# Stage 4: Test - 测试环境镜像
# ============================================
FROM development AS test

USER root

# 安装测试依赖
RUN pip install pytest pytest-asyncio pytest-cov pytest-mock coverage \
    && rm -rf ~/.cache/pip

# 复制测试配置
COPY pytest.ini ./
COPY .coveragerc ./
COPY app/tests ./app/tests

# 创建测试用户并设置权限
RUN chown -R appuser:appuser /app

USER appuser

# 测试命令
CMD ["pytest", "-v", "--cov=app", "--cov-report=term-missing", "--cov-fail-under=80"]

# ============================================
# Labels - 镜像元数据
# ============================================
LABEL org.opencontainers.image.title="PM Digital Employee" \
      org.opencontainers.image.description="项目经理数字员工系统 - 国有大型银行科技子公司项目管理部智能助理" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.vendor="PM Digital Employee Team" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/example/pm-digital-employee" \
      org.opencontainers.image.documentation="https://docs.example.com/pm-digital-employee" \
      org.opencontainers.image.base.name="python:3.11-slim-bookworm" \
      org.opencontainers.image.authors="PM Digital Employee Team" \
      org.opencontainers.image.created="${BUILD_DATE:-2026-03-31}" \
      org.opencontainers.image.security.trusted="true" \
      org.opencontainers.image.security.non-root="true"