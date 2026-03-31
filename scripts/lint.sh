#!/bin/bash
# 项目经理数字员工系统 - 代码检查脚本

set -e

echo "========================================"
echo "项目经理数字员工系统 - 代码检查"
echo "========================================"

# 检查ruff是否安装
if ! command -v ruff &> /dev/null; then
    echo "安装ruff..."
    pip install ruff
fi

# 检查black是否安装
if ! command -v black &> /dev/null; then
    echo "安装black..."
    pip install black
fi

# 检查mypy是否安装
if ! command -v mypy &> /dev/null; then
    echo "安装mypy..."
    pip install mypy
fi

echo ""
echo "运行ruff检查..."
ruff check app/ --config .ruff.toml

echo ""
echo "运行black检查..."
black --check app/ --line-length 100

echo ""
echo "运行mypy检查..."
mypy app/ --config-file mypy.ini || true

echo ""
echo "========================================"
echo "代码检查完成"
echo "========================================"
echo ""

# 统计
ruff_issues=$(ruff check app/ --output-format=count | grep -c "error" || echo 0)
echo "Ruff问题数: $ruff_issues"

if [ "$ruff_issues" -gt 0 ]; then
    echo "建议运行: ./scripts/format.sh"
fi