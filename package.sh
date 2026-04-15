#!/bin/bash
#
# PM Digital Employee - 打包脚本
# 项目经理数字员工系统 - 创建可部署的代码包
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

# 版本号
VERSION="v1.0.0"
PACKAGE_NAME="pm-digital-employee-${VERSION}"
OUTPUT_DIR="${SCRIPT_DIR}/dist"

echo ""
echo "=========================================="
echo "  PM Digital Employee 打包脚本"
echo "  版本: ${VERSION}"
echo "=========================================="
echo ""

# 清理旧的打包文件
clean_old_packages() {
    log_info "清理旧的打包文件..."
    rm -rf "${OUTPUT_DIR}"
    mkdir -p "${OUTPUT_DIR}"
    log_success "清理完成"
}

# 检查必要文件
check_required_files() {
    log_info "检查必要文件..."

    REQUIRED_FILES=(
        "docker-compose.yml"
        "Dockerfile"
        "deploy.sh"
        "update.sh"
        "manage.sh"
        "DEPLOYMENT.md"
        ".env"
        "requirements.txt"
        "app/main.py"
        "app/core/config.py"
    )

    MISSING_FILES=()

    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            MISSING_FILES+=("$file")
        fi
    done

    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        log_error "缺少必要文件:"
        for file in "${MISSING_FILES[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi

    log_success "必要文件检查通过"
}

# 创建临时打包目录
create_temp_dir() {
    log_info "创建临时打包目录..."
    TEMP_DIR="${OUTPUT_DIR}/${PACKAGE_NAME}"
    mkdir -p "${TEMP_DIR}"
    log_success "临时目录创建完成: ${TEMP_DIR}"
}

# 复制项目文件
copy_project_files() {
    log_info "复制项目文件..."

    # 复制核心配置文件
    cp docker-compose.yml "${TEMP_DIR}/"
    cp Dockerfile "${TEMP_DIR}/"
    cp requirements.txt "${TEMP_DIR}/"

    # 复制部署脚本
    cp deploy.sh "${TEMP_DIR}/"
    cp update.sh "${TEMP_DIR}/"
    cp manage.sh "${TEMP_DIR}/"
    cp package.sh "${TEMP_DIR}/"

    # 复制配置文件
    cp .env "${TEMP_DIR}/.env.example"
    cp DEPLOYMENT.md "${TEMP_DIR}/"
    cp README.md "${TEMP_DIR}/" 2>/dev/null || true

    # 复制app目录
    if [ -d "app" ]; then
        cp -r app "${TEMP_DIR}/"
    fi

    # 复制scripts目录
    if [ -d "scripts" ]; then
        cp -r scripts "${TEMP_DIR}/"
    fi

    # 复制prompts目录
    if [ -d "prompts" ]; then
        cp -r prompts "${TEMP_DIR}/"
    fi

    # 复制docs目录
    if [ -d "docs" ]; then
        cp -r docs "${TEMP_DIR}/"
    fi

    # 复制alembic目录（数据库迁移）
    if [ -d "alembic" ]; then
        cp -r alembic "${TEMP_DIR}/"
        cp alembic.ini "${TEMP_DIR}/" 2>/dev/null || true
    fi

    # 复制tests目录
    if [ -d "tests" ] || [ -d "app/tests" ]; then
        mkdir -p "${TEMP_DIR}/tests"
        if [ -d "tests" ]; then
            cp -r tests/* "${TEMP_DIR}/tests/"
        fi
        if [ -d "app/tests" ]; then
            cp -r app/tests/* "${TEMP_DIR}/tests/"
        fi
    fi

    # 复制配置文件
    cp pyproject.toml "${TEMP_DIR}/" 2>/dev/null || true
    cp pytest.ini "${TEMP_DIR}/" 2>/dev/null || true
    cp .ruff.toml "${TEMP_DIR}/" 2>/dev/null || true
    cp mypy.ini "${TEMP_DIR}/" 2>/dev/null || true

    log_success "项目文件复制完成"
}

# 设置文件权限
set_permissions() {
    log_info "设置文件权限..."

    chmod +x "${TEMP_DIR}/deploy.sh"
    chmod +x "${TEMP_DIR}/update.sh"
    chmod +x "${TEMP_DIR}/manage.sh"
    chmod +x "${TEMP_DIR}/package.sh"

    log_success "权限设置完成"
}

# 创建快速启动指南
create_quick_start() {
    log_info "创建快速启动指南..."

    cat > "${TEMP_DIR}/QUICK_START.md" << 'EOF'
# PM Digital Employee 快速启动指南

## 一、上传代码包到服务器

```bash
# 方式1: 使用scp上传
scp pm-digital-employee-v1.0.0.tar.gz user@server:/opt/

# 方式2: 使用rsync上传
rsync -avz pm-digital-employee-v1.0.0.tar.gz user@server:/opt/
```

## 二、解压并部署

```bash
# 登录服务器
ssh user@server

# 解压代码包
cd /opt
tar -xzf pm-digital-employee-v1.0.0.tar.gz
cd pm-digital-employee-v1.0.0

# 配置飞书参数
cp .env.example .env
vim .env
# 修改以下配置:
# LARK_APP_ID=您的飞书应用AppID
# LARK_APP_SECRET=您的飞书应用Secret
# LARK_ENCRYPT_KEY=您设置的加密密钥
# LARK_VERIFICATION_TOKEN=您设置的验证令牌

# 一键部署
./deploy.sh
```

## 三、验证部署

```bash
# 查看服务状态
./manage.sh status

# 查看日志
./manage.sh logs

# 健康检查
curl http://localhost:8000/health
```

## 四、配置飞书回调

1. 登录飞书开放平台: https://open.feishu.cn/
2. 进入应用详情页
3. 设置API接收URL: https://your-domain.com/lark/webhook/event
4. 设置Token和EncodingAESKey（与.env中一致）

## 五、常用运维命令

| 命令 | 说明 |
|------|------|
| `./manage.sh start` | 启动服务 |
| `./manage.sh stop` | 停止服务 |
| `./manage.sh restart` | 重启服务 |
| `./manage.sh logs` | 查看日志 |
| `./manage.sh status` | 查看状态 |
| `./update.sh` | 更新部署 |

---

**详细文档请参考:** DEPLOYMENT.md
EOF

    log_success "快速启动指南创建完成"
}

# 创建版本信息文件
create_version_info() {
    log_info "创建版本信息文件..."

    cat > "${TEMP_DIR}/VERSION.txt" << EOF
PM Digital Employee
项目经理数字员工系统 - 飞书版

版本: ${VERSION}
打包时间: $(date '+%Y-%m-%d %H:%M:%S')
打包主机: $(hostname)

核心功能:
- 项目总览查询
- 项目周报生成
- WBS自动生成
- 任务进度更新
- 飆逸识别与预警
- 成本监控
- 项目制度规范答疑(RAG)
- 项目情况咨询
- 会议纪要生成
- 预立项/立项材料合规初审

用户交互入口: 飞书
技术栈: Python 3.11 + FastAPI + PostgreSQL + Redis + RabbitMQ
EOF

    log_success "版本信息创建完成"
}

# 创建排除文件列表
create_exclude_list() {
    log_info "创建排除文件列表..."

    cat > "${TEMP_DIR}/.deployignore" << 'EOF'
# 部署时忽略的文件
.git/
.github/
.gitignore
*.pyc
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.venv/
venv/
env/
node_modules/
*.log
*.bak
*.tmp
.env.local
*.secret
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db
EOF

    log_success "排除列表创建完成"
}

# 创建压缩包
create_archive() {
    log_info "创建压缩包..."

    cd "${OUTPUT_DIR}"
    tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

    # 计算文件大小
    SIZE=$(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)

    log_success "压缩包创建完成: ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz (${SIZE})"
}

# 清理临时目录
cleanup_temp() {
    log_info "清理临时目录..."
    rm -rf "${TEMP_DIR}"
    log_success "临时目录清理完成"
}

# 显示打包结果
show_result() {
    echo ""
    echo "=========================================="
    echo "        打包完成！"
    echo "=========================================="
    echo ""
    echo "输出文件:"
    echo "  ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
    echo ""
    echo "上传到服务器后执行:"
    echo "  1. tar -xzf ${PACKAGE_NAME}.tar.gz"
    echo "  2. cd ${PACKAGE_NAME}"
    echo "  3. cp .env.example .env && vim .env"
    echo "  4. ./deploy.sh"
    echo ""
    echo "详细部署指南请参考: DEPLOYMENT.md"
    echo ""
}

# 主流程
main() {
    clean_old_packages
    check_required_files
    create_temp_dir
    copy_project_files
    set_permissions
    create_quick_start
    create_version_info
    create_exclude_list
    create_archive
    cleanup_temp
    show_result

    log_success "打包完成！"
}

main "$@"