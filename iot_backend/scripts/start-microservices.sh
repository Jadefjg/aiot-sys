#!/bin/bash
# IoT微服务架构启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "IoT微服务架构启动脚本"
echo "========================================"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: docker-compose未安装"
    exit 1
fi

cd "$PROJECT_ROOT"

# 生成gRPC代码（如果需要）
if [ ! -d "proto/generated" ] || [ -z "$(ls -A proto/generated 2>/dev/null)" ]; then
    echo ">>> 生成gRPC Python代码..."
    cd proto
    ./generate.sh
    cd "$PROJECT_ROOT"
fi

# 构建并启动服务
echo ">>> 构建并启动所有微服务..."
docker-compose -f docker-compose.microservices.yml up -d --build

echo ""
echo "========================================"
echo "服务启动完成！"
echo "========================================"
echo ""
echo "服务端口信息:"
echo "  - Kong API Gateway:  http://localhost:8000"
echo "  - Kong Admin:        http://localhost:8001"
echo "  - Auth Service:      http://localhost:8101"
echo "  - Device Service:    http://localhost:8102"
echo "  - Firmware Service:  http://localhost:8103"
echo "  - EMQX Dashboard:    http://localhost:18083"
echo "  - MQTT Broker:       localhost:1883"
echo ""
echo "gRPC端口:"
echo "  - Auth Service:      localhost:50051"
echo "  - Device Service:    localhost:50052"
echo "  - Firmware Service:  localhost:50053"
echo "  - MQTT Gateway:      localhost:50054"
echo ""
echo "查看日志: docker-compose -f docker-compose.microservices.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.microservices.yml down"
echo ""
