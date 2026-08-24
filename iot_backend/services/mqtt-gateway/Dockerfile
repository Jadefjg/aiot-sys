FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制proto生成的代码
COPY ../proto/generated /app/proto_generated

# 复制应用代码
COPY . .

# 设置Python路径
ENV PYTHONPATH=/app:/app/proto_generated

# 暴露gRPC端口
EXPOSE 50054

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
