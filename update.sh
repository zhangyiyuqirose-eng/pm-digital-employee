#!/bin/bash
#
# PM Digital Employee - 更新部署脚本
# 项目经理数字员工系统 - 拉取最新代码并重新部署
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "=========================================="
echo "  PM Digital Employee 更新部署"
echo "=========================================="
echo ""

# 检查是否有未提交的更改
check_git_status() {
    if [ -d .git ]; then
        if ! git diff-index --quiet HEAD --; then
            log_warning "检测到未提交的更改"
            read -p "是否继续更新？(y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "更新已取消"
                exit 0
            fi
        fi
    fi
}

# 拉取最新代码
pull_code() {
    log_info "拉取最新代码..."

    if [ -d .git ]; then
        git pull origin master 2>/dev/null || git pull origin main 2>/dev/null || {
            log_warning "Git pull 失败，继续使用当前代码"
        }
    else
        log_warning "不是 Git 仓库，跳过代码拉取"
    fi
}

# 备份当前环境
backup_env() {
    log_info "备份环境配置..."

    if [ -f .env ]; then
        cp .env .env.backup.$(date +%Y%m%d%H%M%S)
        log_success "环境配置已备份"
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_success "服务已停止"
}

# 重新构建
rebuild() {
    log_info "重新构建镜像..."
    docker-compose build --no-cache
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose up -d
    log_success "服务已启动"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."

    local max_wait=60
    local wait_time=0

    while [ $wait_time -lt $max_wait ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "服务已就绪！"
            return 0
        fi
        sleep 2
        wait_time=$((wait_time + 2))
        echo -n "."
    done

    echo ""
    log_error "服务启动超时"
    return 1
}

# 显示服务状态
show_status() {
    echo ""
    echo "服务状态:"
    docker-compose ps
    echo ""
    echo "访问地址: http://localhost:8000/docs"
    echo ""
}

# 主流程
main() {
    check_git_status
    backup_env
    pull_code
    stop_services
    rebuild
    start_services
    wait_for_services
    show_status

    log_success "更新部署完成！"
}

main "$@"