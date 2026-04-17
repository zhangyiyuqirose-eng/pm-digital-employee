#!/bin/bash
#
# PM Digital Employee - 一键部署脚本
# 项目经理数字员工系统 - 飞书版
#
# 使用方法: chmod +x deploy.sh && ./deploy.sh
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统
check_system() {
    log_info "检查系统环境..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        log_info "操作系统: $OS $VER"
    else
        log_error "无法检测操作系统"
        exit 1
    fi
}

# 检查并安装依赖
install_dependencies() {
    log_info "检查并安装系统依赖..."

    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3 python3-pip python3-venv git curl
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip git curl
    elif command -v dnf &> /dev/null; then
        dnf install -y python3 python3-pip git curl
    else
        log_error "不支持的包管理器"
        exit 1
    fi

    log_success "系统依赖安装完成"
}

# 安装 Docker
install_docker() {
    log_info "检查 Docker..."

    if command -v docker &> /dev/null; then
        log_success "Docker 已安装"
        docker --version
        return 0
    fi

    log_info "安装 Docker..."

    curl -fsSL https://get.docker.com | sh

    # 启动 Docker
    systemctl start docker
    systemctl enable docker

    # 添加当前用户到 docker 组
    usermod -aG docker $USER 2>/dev/null || true

    log_success "Docker 安装完成"
}

# 安装 Docker Compose
install_docker_compose() {
    log_info "检查 Docker Compose..."

    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose 已安装"
        docker-compose --version
        return 0
    fi

    log_info "安装 Docker Compose..."

    curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    log_success "Docker Compose 安装完成"
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量配置..."

    if [ -f .env ]; then
        log_warning ".env 文件已存在，跳过创建"
        return 0
    fi

    if [ -f .env.example ]; then
        cp .env.example .env
        log_success "已从 .env.example 创建 .env 文件"
        log_warning "请编辑 .env 文件，配置飞书参数！"
    else
        log_error ".env.example 文件不存在"
        exit 1
    fi
}

# 配置飞书参数
configure_lark() {
    log_info "配置飞书参数..."

    if [ -z "$LARK_APP_ID" ]; then
        log_warning "未设置环境变量，请手动编辑 .env 文件"
        return 0
    fi

    # 更新 .env 文件
    sed -i "s/^LARK_APP_ID=.*/LARK_APP_ID=$LARK_APP_ID/" .env 2>/dev/null || true
    sed -i "s/^LARK_APP_SECRET=.*/LARK_APP_SECRET=$LARK_APP_SECRET/" .env 2>/dev/null || true
    sed -i "s/^LARK_ENCRYPT_KEY=.*/LARK_ENCRYPT_KEY=$LARK_ENCRYPT_KEY/" .env 2>/dev/null || true
    sed -i "s/^LARK_VERIFICATION_TOKEN=.*/LARK_VERIFICATION_TOKEN=$LARK_VERIFICATION_TOKEN/" .env 2>/dev/null || true

    log_success "飞书参数配置完成"
}

# 构建Docker镜像
build_docker() {
    log_info "构建 Docker 镜像..."

    docker-compose build --no-cache

    log_success "Docker 镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    docker-compose up -d

    log_success "服务启动完成"
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

# 显示部署信息
show_deploy_info() {
    echo ""
    echo "=========================================="
    echo "        部署完成！"
    echo "=========================================="
    echo ""
    echo "服务地址:"
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo "  - API 根路径: http://localhost:8000/"
    echo ""
    echo "飞书回调地址:"
    echo "  - Webhook: https://your-domain.com/lark/webhook/event"
    echo "  - Card Callback: https://your-domain.com/lark/callback/card"
    echo ""
    echo "常用命令:"
    echo "  - 查看日志: docker-compose logs -f app"
    echo "  - 重启服务: docker-compose restart"
    echo "  - 停止服务: docker-compose down"
    echo "  - 查看状态: docker-compose ps"
    echo ""
    echo "下一步操作:"
    echo "  1. 编辑 .env 文件，配置飞书参数"
    echo "  2. 配置飞书开放平台的回调URL"
    echo "  3. 在飞书中测试机器人功能"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  PM Digital Employee 一键部署脚本"
    echo "  项目经理数字员工系统 - 飞书版"
    echo "=========================================="
    echo ""

    # 检查是否为 root 用户
    if [ "$EUID" -ne 0 ]; then
        log_warning "建议使用 root 用户执行此脚本"
        log_info "如遇权限问题，请使用 sudo 重新执行"
    fi

    # 执行部署步骤
    check_system
    install_dependencies
    install_docker
    install_docker_compose
    create_env_file
    configure_lark
    build_docker
    start_services
    wait_for_services
    show_deploy_info
}

# 执行主函数
main "$@"