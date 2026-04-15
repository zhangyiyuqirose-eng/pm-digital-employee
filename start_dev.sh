#!/bin/bash
# PM Digital Employee - 本地开发启动脚本
# 一键启动本地开发环境

set -e

echo "==========================================="
echo "  PM数字员工系统 - 本地开发启动脚本"
echo "==========================================="

# 检查Python环境
echo "检查Python环境..."
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python"
    exit 1
fi

PYTHON_VERSION=$(python --version)
echo "Python版本: $PYTHON_VERSION"

# 检查虚拟环境
if [[ -d "venv" ]]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
elif [[ -d "../venv" ]]; then
    echo "激活上级目录虚拟环境..."
    source ../venv/bin/activate
else
    echo "警告: 未找到虚拟环境，使用系统Python环境"
fi

# 检查依赖
echo "检查依赖..."
MISSING_DEPS=()

# 检查必需的包
REQUIRED_PACKAGES=(
    "fastapi"
    "uvicorn"
    "sqlalchemy"
    "pydantic"
    "redis"
    "celery"
    "httpx"
    "openai"
    "anthropic"
)

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" &> /dev/null; then
        MISSING_DEPS+=("$package")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "警告: 发现缺失的依赖: ${MISSING_DEPS[*]}"
    echo "尝试安装 requirements.txt 中的依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt || echo "依赖安装失败，请检查网络连接"
    else
        echo "未找到 requirements.txt 文件"
    fi
else
    echo "所有必需依赖均已安装"
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "复制环境变量配置模板..."
        cp .env.example .env
        echo "请编辑 .env 文件以配置飞书参数"
    else
        echo "警告: 未找到 .env 和 .env.example 文件"
    fi
fi

# 检查并创建必要目录
mkdir -p logs
mkdir -p uploads

echo "启动PM数字员工系统..."

# 使用uvicorn启动应用
if command -v uvicorn &> /dev/null; then
    echo "使用uvicorn启动服务..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "uvicorn未安装，尝试直接运行..."
    python -m app.main
fi

echo "服务已启动!"
echo "访问 http://localhost:8000 查看应用"
echo "访问 http://localhost:8000/docs 查看API文档"