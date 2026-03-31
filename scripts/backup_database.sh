#!/bin/bash
# 项目经理数字员工系统 - 数据库备份脚本

set -e

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 配置
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-pm_user}
DB_NAME=${DB_NAME:-pm_digital_employee}
BACKUP_DIR=${BACKUP_DIR:-./backups}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pm_${DATE}.sql"

echo "========================================"
echo "项目经理数字员工系统 - 数据库备份"
echo "========================================"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "备份信息:"
echo "  - 数据库: $DB_NAME"
echo "  - 用户: $DB_USER"
echo "  - 主机: $DB_HOST:$DB_PORT"
echo "  - 备份文件: $BACKUP_FILE"
echo ""

# 执行备份
echo "开始备份..."
if docker ps | grep -q postgres; then
    # Docker环境
    docker exec pm_postgres pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
else
    # 本地环境
    pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME > $BACKUP_FILE
fi

# 检查备份文件
if [ -f "$BACKUP_FILE" ]; then
    size=$(ls -lh $BACKUP_FILE | awk '{print $5}')
    echo "备份完成: $BACKUP_FILE ($size)"
else
    echo "备份失败"
    exit 1
fi

# 压缩备份
echo "压缩备份..."
gzip $BACKUP_FILE
BACKUP_GZ="${BACKUP_FILE}.gz"
size_gz=$(ls -lh $BACKUP_GZ | awk '{print $5}')
echo "压缩完成: $BACKUP_GZ ($size_gz)"

# 清理旧备份（保留30天）
echo "清理旧备份..."
find $BACKUP_DIR -name "pm_*.sql.gz" -mtime +30 -delete
remaining=$(ls -1 $BACKUP_DIR/*.sql.gz 2>/dev/null | wc -l)
echo "保留备份文件: $remaining 个"

echo ""
echo "========================================"
echo "备份完成"
echo "========================================"
echo ""
echo "恢复命令:"
echo "  gunzip -c $BACKUP_GZ | docker exec -i pm_postgres psql -U $DB_USER $DB_NAME"