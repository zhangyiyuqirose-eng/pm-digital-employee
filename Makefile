# PM Digital Employee Makefile
# 项目经理数字员工系统 - 开发命令集合

.PHONY: help install dev test test-cov lint format type-check clean docker-up docker-down db-init db-migrate health-check

# 默认目标
.DEFAULT_GOAL := help

# ============================================
# 开发环境
# ============================================

install: ## 安装依赖
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev: ## 启动开发服务器（热重载）
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-celery: ## 启动Celery Worker
	celery -A app.tasks.celery_app worker --loglevel=info

dev-celery-beat: ## 启动Celery Beat调度器
	celery -A app.tasks.celery_app beat --loglevel=info

# ============================================
# 测试
# ============================================

test: ## 运行所有测试
	pytest tests/ -v

test-cov: ## 运行测试并生成覆盖率报告
	pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

test-unit: ## 运行单元测试
	pytest tests/ -v -m "unit"

test-integration: ## 运行集成测试
	pytest tests/ -v -m "integration"

test-e2e: ## 运行E2E测试
	pytest tests/e2e/ -v

# ============================================
# 代码质量
# ============================================

lint: ## 运行Ruff检查
	ruff check app/ tests/ --config .ruff.toml

lint-fix: ## 自动修复Ruff问题
	ruff check app/ tests/ --fix --config .ruff.toml

format: ## 格式化代码（Black）
	black app/ tests/ --line-length 100

format-check: ## 检查格式（不修改）
	black app/ tests/ --check --line-length 100

type-check: ## 类型检查（MyPy）
	mypy app/ --config-file mypy.ini

security: ## 安全检查（Bandit）
	bandit -r app/ -ll

quality: lint format-check type-check ## 运行所有质量检查

# ============================================
# Docker
# ============================================

docker-build: ## 构建Docker镜像
	docker-compose build

docker-up: ## 启动所有Docker服务
	docker-compose up -d

docker-down: ## 停止所有Docker服务
	docker-compose down

docker-logs: ## 查看Docker日志
	docker-compose logs -f app

docker-restart: ## 重启Docker服务
	docker-compose restart

docker-clean: ## 清理Docker容器和镜像
	docker-compose down -v --rmi all

# ============================================
# 数据库
# ============================================

db-init: ## 初始化数据库（创建扩展+迁移）
	python scripts/init_db.py

db-migrate: ## 执行数据库迁移
	alembic upgrade head

db-migrate-down: ## 回退一个版本
	alembic downgrade -1

db-migration-create: ## 创建新迁移
	alembic revision --autogenerate -m "$(MSG)"

db-seed: ## 生成演示数据
	python scripts/seed_demo_data.py

db-reset: ## 重置数据库（慎用）
	alembic downgrade base
	alembic upgrade head
	python scripts/seed_demo_data.py

# ============================================
# 运维脚本
# ============================================

health-check: ## 健康检查
	bash scripts/health_check.sh

bootstrap: ## 系统初始化
	bash scripts/bootstrap.sh

backup: ## 备份数据库
	bash scripts/backup_database.sh

# ============================================
# 预提交
# ============================================

pre-commit: ## 运行pre-commit检查
	pre-commit run --all-files

pre-commit-install: ## 安装pre-commit hooks
	pre-commit install

# ============================================
# 清理
# ============================================

clean: ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

# ============================================
# 帮助
# ============================================

help: ## 显示帮助信息
	@echo "PM Digital Employee - Makefile 命令列表"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'