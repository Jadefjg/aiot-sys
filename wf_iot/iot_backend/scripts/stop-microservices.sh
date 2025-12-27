#!/bin/bash
# IoT微服务架构停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "IoT微服务架构停止脚本"
echo "========================================"

cd "$PROJECT_ROOT"

echo ">>> 停止所有微服务..."
docker-compose -f docker-compose.microservices.yml down

echo ""
echo "所有服务已停止"
echo ""
echo "如需清理数据卷，请运行:"
echo "docker-compose -f docker-compose.microservices.yml down -v"
echo ""
