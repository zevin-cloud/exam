#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

ACTION=${1:-"up"}

case "$ACTION" in
  build)
    echo "🔨 正在构建 Docker 镜像 (FastAPI 一体化镜像)..."
    docker compose build
    echo "✅ 构建完成！"
    ;;
  up|start)
    echo "🚀 正在构建并启动服务 (MySQL 8.0 + FastAPI 一体化应用)..."
    docker compose up -d --build --force-recreate
    
    # 动态获取对外端口与主机 IP
    PORT_VAL=$(grep "^PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '\r ' || echo "")
    PORT_VAL=${PORT_VAL:-8000}
    HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -z "$HOST_IP" ] && HOST_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}')
    HOST_IP=${HOST_IP:-"localhost"}

    echo ""
    echo "=========================================================="
    echo "🎉 考务系统已在后台运行！"
    echo "🌐 局域网/公网访问: http://${HOST_IP}:${PORT_VAL}"
    echo "🌐 本机访问:       http://localhost:${PORT_VAL}"
    echo "📑 接口文档地址:   http://${HOST_IP}:${PORT_VAL}/docs"
    echo "=========================================================="
    docker compose ps
    ;;
  down|stop)
    echo "🛑 正在停止考务系统容器..."
    docker compose down
    echo "✅ 服务已停止！"
    ;;
  restart)
    echo "🔄 正在重启考务系统..."
    docker compose restart
    echo "✅ 重启成功！"
    ;;
  logs)
    docker compose logs -f app
    ;;
  logs-all)
    docker compose logs -f
    ;;
  backup)
    mkdir -p "$DIR/backups"
    BACKUP_FILE="$DIR/backups/exam_db_$(date +%Y%m%d_%H%M%S).sql"
    echo "📦 正在备份 MySQL 数据库到 $BACKUP_FILE ..."
    docker compose exec -T mysql mysqldump -u root -proot123456 exam_db > "$BACKUP_FILE"
    echo "✅ 备份成功！文件大小: $(du -sh "$BACKUP_FILE" | cut -f1)"
    ;;
  *)
    echo "使用帮助:"
    echo "  bash deploy.sh start    - 构建并启动系统 (默认)"
    echo "  bash deploy.sh stop     - 停止系统"
    echo "  bash deploy.sh restart  - 重启系统"
    echo "  bash deploy.sh logs     - 实时查看应用日志"
    echo "  bash deploy.sh build    - 仅重新构建镜像"
    echo "  bash deploy.sh backup   - 一键备份 MySQL 数据"
    ;;
esac
