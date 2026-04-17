# PM Digital Employee - Production Dockerfile
# 项目经理数字员工系统 - 生产级Docker镜像

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim AS production

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r pmuser && useradd -r -g pmuser pmuser

# 创建必要的目录
RUN mkdir -p /app /var/log/pm_digital_employee /app/data \
    && chown -R pmuser:pmuser /app /var/log/pm_digital_employee

# 设置工作目录
WORKDIR /app

# 从builder复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制应用代码
COPY --chown=pmuser:pmuser app/ /app/app/
COPY --chown=pmuser:pmuser scripts/ /app/scripts/
COPY --chown=pmuser:pmuser prompts/ /app/prompts/

# 复制配置文件
COPY --chown=pmuser:pmuser pyproject.toml /app/
COPY --chown=pmuser:pmuser README.md /app/

# 切换到非root用户
USER pmuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（单worker以支持WebSocket长连接进程）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# Stage 3: Development
# ============================================
FROM production AS development

USER root

# 安装开发依赖
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    ruff \
    black \
    mypy

USER pmuser

# 开发模式启动命令（单进程，支持热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]