#!/bin/bash
# gRPC Python代码生成脚本
# 使用方法: ./generate.sh

PROTO_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$PROTO_DIR/generated"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 检查grpcio-tools是否安装
if ! python3 -c "import grpc_tools.protoc" 2>/dev/null; then
    echo "Installing grpcio-tools..."
    pip3 install grpcio-tools
fi

# 生成Python代码
echo "Generating Python gRPC code..."

python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/auth.proto"

python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/device.proto"

python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/mqtt_gateway.proto"

python3 -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/firmware.proto"

# 创建__init__.py
touch "$OUTPUT_DIR/__init__.py"

# 修复import路径问题
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    find "$OUTPUT_DIR" -name "*_pb2_grpc.py" -exec sed -i '' 's/^import \(.*\)_pb2/from . import \1_pb2/' {} \;
else
    # Linux
    find "$OUTPUT_DIR" -name "*_pb2_grpc.py" -exec sed -i 's/^import \(.*\)_pb2/from . import \1_pb2/' {} \;
fi

echo "Done! Generated files in: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
