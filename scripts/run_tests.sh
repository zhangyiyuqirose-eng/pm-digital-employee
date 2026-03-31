#!/bin/bash
# 项目经理数字员工系统 - 测试运行脚本

set -e

echo "========================================"
echo "项目经理数字员工系统 - 运行测试"
echo "========================================"

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置测试环境变量
export TESTING=true

# 参数
COVERAGE=${COVERAGE:-true}
VERBOSE=${VERBOSE:-true}
TEST_TYPE=${TEST_TYPE:-all}

echo "测试配置:"
echo "  - Coverage: $COVERAGE"
echo "  - Verbose: $VERBOSE"
echo "  - Test Type: $TEST_TYPE"
echo ""

# 构建pytest命令
PYTEST_CMD="pytest"

if [ "$VERBOSE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term --cov-report=html:coverage_report"
fi

# 根据测试类型选择测试
case $TEST_TYPE in
    unit)
        PYTEST_CMD="$PYTEST_CMD -m unit"
        ;;
    integration)
        PYTEST_CMD="$PYTEST_CMD -m integration"
        ;;
    e2e)
        PYTEST_CMD="$PYTEST_CMD -m e2e"
        ;;
    all)
        PYTEST_CMD="$PYTEST_CMD"
        ;;
    *)
        echo "未知的测试类型: $TEST_TYPE"
        exit 1
        ;;
esac

echo "运行命令: $PYTEST_CMD"
echo ""

# 运行测试
$PYTEST_CMD

# 检查结果
echo ""
echo "========================================"
echo "测试完成"
echo "========================================"

if [ "$COVERAGE" = "true" ]; then
    echo ""
    echo "Coverage报告已生成: coverage_report/index.html"
fi