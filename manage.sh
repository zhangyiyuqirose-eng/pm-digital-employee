#!/bin/bash
#
# PM Digital Employee - 服务管理脚本
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$1" in
    start)
        echo "启动服务..."
        docker compose up -d
        echo "服务已启动"
        ;;
    stop)
        echo "停止服务..."
        docker compose down
        echo "服务已停止"
        ;;
    restart)
        echo "重启服务..."
        docker compose restart
        echo "服务已重启"
        ;;
    logs)
        docker compose logs -f ${2:-app}
        ;;
    status)
        echo "服务状态:"
        docker compose ps
        echo ""
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "服务未就绪"
        ;;
    build)
        echo "构建镜像..."
        docker compose build --no-cache
        echo "构建完成"
        ;;
    ps)
        docker compose ps
        ;;
    *)
        echo "PM Digital Employee 服务管理"
        echo ""
        echo "用法: $0 {start|stop|restart|logs|status|build|ps}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  logs    - 查看日志 (可指定服务名: logs app)"
        echo "  status  - 查看服务状态"
        echo "  build   - 重新构建镜像"
        echo "  ps      - 查看容器状态"
        ;;
esac
