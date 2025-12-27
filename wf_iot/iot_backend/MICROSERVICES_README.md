# IoT微服务架构

## 架构概述

本项目采用微服务架构，将原有单体应用拆分为4个独立服务：

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kong API Gateway (:8000)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│  Auth Service │   │ Device Service  │   │  Firmware Service   │
│  :8101/50051  │   │  :8102/50052    │   │    :8103/50053      │
└───────────────┘   └─────────────────┘   └─────────────────────┘
        │                     │                     │
        │              ┌──────┴──────┐              │
        │              │             │              │
        │              ▼             ▼              │
        │      ┌─────────────┐   ┌──────────────┐   │
        │      │MQTT Gateway │   │Celery Worker │   │
        │      │   :50054    │   │ (firmware)   │   │
        │      └─────────────┘   └──────────────┘   │
        │              │                            │
        ▼              ▼                            ▼
┌───────────────────────────────────────────────────────────────┐
│                        基础设施                                │
│  MySQL(Auth:3307, Device:3308, Firmware:3309)                 │
│  Redis:6379    │    EMQX:1883/18083                           │
└───────────────────────────────────────────────────────────────┘
```

## 服务说明

### Auth Service (认证授权服务)
- **HTTP端口**: 8101
- **gRPC端口**: 50051
- **功能**: 用户认证、JWT令牌管理、角色权限管理
- **数据库**: iot_auth (MySQL 3307)

### Device Service (设备管理服务)
- **HTTP端口**: 8102
- **gRPC端口**: 50052
- **功能**: 设备CRUD、设备状态管理、设备数据采集
- **数据库**: iot_device (MySQL 3308)

### Firmware Service (固件管理服务)
- **HTTP端口**: 8103
- **gRPC端口**: 50053
- **功能**: 固件上传、版本管理、OTA升级任务
- **数据库**: iot_firmware (MySQL 3309)

### MQTT Gateway (MQTT网关)
- **gRPC端口**: 50054
- **功能**: MQTT消息转发、设备指令下发、事件发布

## 通信方式

### gRPC (同步通信)
- Auth Service ← Device Service: Token验证、权限检查
- Auth Service ← Firmware Service: Token验证、权限检查
- MQTT Gateway ← Device Service: 设备指令下发
- MQTT Gateway ← Firmware Service: 固件升级指令

### Redis Pub/Sub (异步事件)
- `iot:device:status`: 设备状态变更事件
- `iot:device:data`: 设备数据上报事件
- `iot:firmware:upgrade`: 固件升级事件

## 快速启动

### 前置条件
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (用于开发)

### 启动所有服务

```bash
# 使用启动脚本
./scripts/start-microservices.sh

# 或手动启动
docker-compose -f docker-compose.microservices.yml up -d --build
```

### 停止服务

```bash
# 使用停止脚本
./scripts/stop-microservices.sh

# 或手动停止
docker-compose -f docker-compose.microservices.yml down

# 停止并清理数据
docker-compose -f docker-compose.microservices.yml down -v
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.microservices.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.microservices.yml logs -f auth-service
```

## API访问

所有API通过Kong网关统一访问：

```bash
# 通过Kong网关访问
curl http://localhost:8000/api/v1/auth/login

# 直接访问服务（开发调试用）
curl http://localhost:8101/api/v1/auth/login
```

### API文档
- Auth Service: http://localhost:8101/docs
- Device Service: http://localhost:8102/docs
- Firmware Service: http://localhost:8103/docs

### 健康检查
```bash
curl http://localhost:8101/health
curl http://localhost:8102/health
curl http://localhost:8103/health
```

## 开发指南

### 本地开发

1. 安装依赖：
```bash
cd services/auth-service
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

2. 生成gRPC代码：
```bash
cd proto
./generate.sh
```

3. 启动服务：
```bash
cd services/auth-service
uvicorn app.main:app --host 0.0.0.0 --port 8101 --reload
```

### 添加新服务

1. 在 `proto/` 创建新的 `.proto` 文件
2. 运行 `./proto/generate.sh` 生成gRPC代码
3. 在 `services/` 创建新服务目录
4. 实现服务代码
5. 更新 `docker-compose.microservices.yml`
6. 更新 `kong/kong.yml` 添加路由

## 目录结构

```
iot_backend/
├── docker-compose.microservices.yml  # 微服务Docker编排
├── init-databases.sql                # 数据库初始化
├── kong/
│   ├── kong.yml                      # Kong声明式配置
│   └── kong.conf                     # Kong配置文件
├── proto/
│   ├── auth.proto                    # Auth服务Proto
│   ├── device.proto                  # Device服务Proto
│   ├── firmware.proto                # Firmware服务Proto
│   ├── mqtt_gateway.proto            # MQTT Gateway Proto
│   ├── generate.sh                   # gRPC代码生成脚本
│   └── generated/                    # 生成的Python代码
├── scripts/
│   ├── start-microservices.sh        # 启动脚本
│   └── stop-microservices.sh         # 停止脚本
└── services/
    ├── auth-service/                 # 认证服务
    ├── device-service/               # 设备服务
    ├── firmware-service/             # 固件服务
    └── mqtt-gateway/                 # MQTT网关
```

## 环境变量

参考 `.env.microservices.example` 文件配置环境变量。

## 常见问题

### 服务启动失败
1. 检查Docker是否运行
2. 检查端口是否被占用
3. 查看服务日志定位问题

### gRPC连接失败
1. 确认目标服务已启动
2. 检查网络配置
3. 确认gRPC端口正确

### 数据库连接失败
1. 等待数据库容器完全启动
2. 检查数据库连接字符串
3. 确认数据库用户权限
