#!/bin/bash
# 项目经理数字员工系统 - 一键初始化脚本

set -e

echo "========================================"
echo "项目经理数字员工系统 - 一键初始化"
echo "========================================"

# 检查环境变量
echo "检查环境变量..."
if [ ! -f ".env" ]; then
    echo "警告: .env文件不存在，请从.env.example复制并配置"
    cp .env.example .env
    echo "已创建.env文件，请修改配置后重新运行"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 创建必要的目录
echo "创建目录..."
mkdir -p logs
mkdir -p data
mkdir -p backups

# 检查Docker
echo "检查Docker..."
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 启动基础服务
echo "启动基础服务..."
docker-compose up -d postgres redis rabbitmq

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
until docker exec postgres pg_isready -U ${DB_USER:-pm_user}; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

until docker exec redis redis-cli ping | grep -q PONG; do
    echo "等待Redis启动..."
    sleep 2
done

echo "基础服务已启动"

# 数据库迁移
echo "执行数据库迁移..."
if [ -d "alembic" ]; then
    docker-compose run --rm app alembic upgrade head
else
    echo "警告: alembic目录不存在，跳过迁移"
fi

# 导入种子数据
echo "导入种子数据..."
if [ -f "scripts/seed_demo_data.py" ]; then
    docker-compose run --rm app python scripts/seed_demo_data.py
else
    echo "警告: 种子数据脚本不存在，跳过"
fi

# 导入知识库
echo "导入知识库..."
if [ -f "scripts/import_knowledge.py" ] && [ -d "prompts" ]; then
    docker-compose run --rm app python scripts/import_knowledge.py --source prompts
else
    echo "警告: 知识库导入脚本不存在，跳过"
fi

# 启动应用服务
echo "启动应用服务..."
docker-compose up -d app celery_worker celery_beat

# 等待应用启动
echo "等待应用启动..."
sleep 5

# 健康检查
echo "执行健康检查..."
until curl -s http://localhost:8000/health | grep -q healthy; do
    echo "等待应用启动..."
    sleep 2
done

echo "========================================"
echo "初始化完成！"
echo "========================================"
echo ""
echo "服务状态:"
docker-compose ps
echo ""
echo "访问地址:"
echo "  - API: http://localhost:8000"
echo "  - 健康检查: http://localhost:8000/health"
echo ""
echo "下一步:"
echo "  1. 配置飞书Webhook地址"
echo "  2. 导入项目数据"
echo "  3. 配置知识库内容"
echo ""
echo "完成！"