#!/bin/bash
# 项目经理数字员工系统 - 健康检查脚本

echo "========================================"
echo "项目经理数字员工系统 - 健康检查"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_service() {
    name=$1
    url=$2
    expected=$3

    response=$(curl -s $url)
    status=$?

    if [ $status -eq 0 ] && echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}[OK]${NC} $name - 正常"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name - 异常"
        return 1
    fi
}

check_container() {
    name=$1

    status=$(docker inspect --format='{{.State.Status}}' $name 2>/dev/null)

    if [ "$status" = "running" ]; then
        echo -e "${GREEN}[OK]${NC} $name - 运行中"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name - 未运行 ($status)"
        return 1
    fi
}

# 检查Docker容器
echo "检查Docker容器..."
check_container "pm_postgres" || true
check_container "pm_redis" || true
check_container "pm_rabbitmq" || true
check_container "pm_app" || true
check_container "pm_celery_worker" || true

echo ""

# 检查服务端点
echo "检查服务端点..."
check_service "API健康" "http://localhost:8000/health" "healthy" || true
check_service "API就绪" "http://localhost:8000/ready" "ready" || true
check_service "API存活" "http://localhost:8000/live" "alive" || true

echo ""

# 检查数据库
echo "检查数据库连接..."
db_response=$(docker exec pm_postgres pg_isready -U pm_user 2>/dev/null)
if echo "$db_response" | grep -q "accepting connections"; then
    echo -e "${GREEN}[OK]${NC} PostgreSQL - 接受连接"
else
    echo -e "${RED}[FAIL]${NC} PostgreSQL - 连接异常"
fi

echo ""

# 检查Redis
echo "检查Redis连接..."
redis_response=$(docker exec pm_redis redis-cli ping 2>/dev/null)
if [ "$redis_response" = "PONG" ]; then
    echo -e "${GREEN}[OK]${NC} Redis - 正常响应"
else
    echo -e "${RED}[FAIL]${NC} Redis - 连接异常"
fi

echo ""

# 检查RabbitMQ
echo "检查RabbitMQ连接..."
rabbitmq_status=$(docker exec pm_rabbitmq rabbitmqctl status 2>/dev/null | grep -c "running")
if [ "$rabbitmq_status" -gt 0 ]; then
    echo -e "${GREEN}[OK]${NC} RabbitMQ - 运行中"
else
    echo -e "${RED}[FAIL]${NC} RabbitMQ - 连接异常"
fi

echo ""

# 检查Celery
echo "检查Celery Worker..."
celery_active=$(docker exec pm_celery_worker celery -A app.tasks.celery_app inspect active 2>/dev/null | grep -c "ok")
if [ "$celery_active" -gt 0 ]; then
    echo -e "${GREEN}[OK]${NC} Celery Worker - 正常"
else
    echo -e "${YELLOW}[WARN]${NC} Celery Worker - 可能未运行或无活跃任务"
fi

echo ""

# 总结
echo "========================================"
echo "健康检查完成"
echo "========================================"

# 返回状态码
failed=$(docker-compose ps | grep -c "Exit" || echo 0)
if [ "$failed" -gt 0 ]; then
    echo -e "${RED}存在异常服务，请检查日志${NC}"
    exit 1
else
    echo -e "${GREEN}所有服务正常${NC}"
    exit 0
fi