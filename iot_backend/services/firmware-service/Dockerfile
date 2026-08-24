FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制proto生成的代码
COPY ../proto/generated /app/proto_generated

# 复制应用代码
COPY . .

# 创建固件存储目录
RUN mkdir -p /app/firmware_storage

# 设置Python路径
ENV PYTHONPATH=/app:/app/proto_generated

# 暴露端口
EXPOSE 8103 50053

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8103"]
