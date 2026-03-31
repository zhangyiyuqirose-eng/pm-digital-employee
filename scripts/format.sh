#!/bin/bash
# 项目经理数字员工系统 - 代码格式化脚本

set -e

echo "========================================"
echo "项目经理数字员工系统 - 代码格式化"
echo "========================================"

# 检查工具是否安装
if ! command -v ruff &> /dev/null; then
    echo "安装ruff..."
    pip install ruff
fi

if ! command -v black &> /dev/null; then
    echo "安装black..."
    pip install black
fi

echo ""
echo "运行ruff格式化..."
ruff format app/ --config .ruff.toml

echo ""
echo "运行ruff修复..."
ruff check app/ --fix --config .ruff.toml

echo ""
echo "运行black格式化..."
black app/ --line-length 100

echo ""
echo "========================================"
echo "格式化完成"
echo "========================================"
echo ""
echo "建议: 再次运行 ./scripts/lint.sh 检查剩余问题"