#!/bin/bash
# PM数字员工 - 飞书长连接服务启动脚本

set -e

PROJECT_DIR="/data/disk/projects/pm-digital-employee"
SCRIPT_NAME="lark_ws_client.py"

cd $PROJECT_DIR

echo "========================================"
echo "PM数字员工 - 飞书长连接服务"
echo "========================================"
echo "目录: $PROJECT_DIR"
echo "脚本: $SCRIPT_NAME"
echo ""

# 检查.env配置
if [ -z "$(grep LARK_APP_ID .env | grep -v cli_a1b2c3d4)" ]; then
    echo "警告: LARK_APP_ID 可能是示例值，请检查.env配置"
fi

echo "正在启动飞书长连接客户端..."
echo ""

# 运行Python脚本
python3 scripts/$SCRIPT_NAME