
# 部署与运维考虑

#【1-Nginx配置】


#【2-docker-compose.yml】


#【3-数据库迁移】
# 1.数据库迁移: pip install alembic

# 2.初始化：alembic init migrations

# 3.配置 alembic.ini: 修改 sqlalchemy.url 指向你的MySQL数据库

# 4.在 env.py 中导⼊Base： from app.db.base import Base; target_metadata = Base.metadata

# 5.生成迁移脚本：alembic revision ----autogenerate -m "Initial migration"

# 6.执行迁移：alembic upgrade head

# 7.维护








⏺ 根据我对项目的深入分析，以下是各模块的微服务间通信需求：

  模块间通信需求分析

  1. 当前架构状态

  当前项目是单体架构，各模块通过内部函数调用和数据库关联进行通信。若要拆分为微服务，需要以下通信：

  2. 推荐的微服务划分与通信

  ┌─────────────────────────────────────────────────────────────────┐
  │                        API Gateway                               │
  └─────────────────────────────────────────────────────────────────┘
                                │
       ┌────────────┬───────────┼───────────┬────────────┐
       ▼            ▼           ▼           ▼            ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │  认证    │  │  用户    │  │  设备    │  │  固件    │  │ 消息推送 │
  │  服务    │  │  服务    │  │  服务    │  │  服务    │  │  服务   │
  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
       │            │           │           │            │
       └────────────┴───────────┴───────────┴────────────┘
                                │
                      ┌─────────┴─────────┐
                      │   消息队列 (MQTT/  │
                      │   Redis/RabbitMQ) │
                      └───────────────────┘

  3. 具体通信需求

  | 调用方         | 被调用方     | 通信场景                       | 推荐方式       |
  |----------------|--------------|--------------------------------|----------------|
  | 设备服务 →     | 用户服务     | 验证设备归属权 device.owner_id | 同步 HTTP/gRPC |
  | 设备服务 →     | 认证服务     | 权限检查 has_permission()      | 同步 HTTP/gRPC |
  | 固件服务 →     | 设备服务     | 检查设备是否存在、获取设备信息 | 同步 HTTP/gRPC |
  | 固件服务 →     | 消息推送服务 | 发送固件升级命令               | 异步 消息队列  |
  | 设备服务 →     | 消息推送服务 | 发送设备控制命令               | 异步 消息队列  |
  | 消息推送服务 → | 设备服务     | 更新设备状态/上报数据          | 异步 消息队列  |

  4. 核心通信链路

  【链路1：权限验证】(同步，高频)
  任意服务请求 → 认证服务 (JWT验证)
                   → 用户服务 (获取用户权限)
                      → 返回权限列表

  【链路2：设备命令下发】(异步)
  API请求 → 设备服务 → MQ → MQTT服务 → 物联网设备
                              ↓
                       命令响应回调 → 设备服务更新状态

  【链路3：固件升级】(异步，长时任务)
  API请求 → 固件服务 → 创建任务 → Celery Worker
                                ↓
                        MQTT发送升级包 → 设备
                                ↓
                        状态回调 → 更新任务进度

  5. 建议的拆分方案

  | 微服务名称       | 包含模块                       | 通信方式                  |
  |------------------|--------------------------------|---------------------------|
  | auth-service     | 认证 + 用户 + 角色 + 权限      | HTTP REST / gRPC          |
  | device-service   | 设备管理 + 设备数据 + 设备命令 | HTTP + 消息队列           |
  | firmware-service | 固件管理 + 升级任务            | HTTP + Celery             |
  | mqtt-gateway     | MQTT消息收发                   | 消息队列 (Redis/RabbitMQ) |

  6. 关键注意点

  1. 用户-角色-权限 建议合并为一个认证服务，避免过度拆分导致的高频RPC调用
  2. 设备→固件 需要通信：升级任务需要验证设备存在
  3. MQTT服务 应独立为消息网关，通过消息队列与其他服务解耦
  4. Celery任务 可保持在固件服务内部，或独立为任务调度服务

  当前代码中的跨模块调用点（需要改造为服务间通信）：
  - app/api/v1/endpoints/devices.py:88 - 检查用户权限
  - app/api/v1/endpoints/firmware.py - 检查设备存在性
  - app/services/mqtt_service.py - 更新设备状态调用device_crud




 概述

     将当前单体FastAPI应用拆分为4个独立微服务，实现服务间通信、API Gateway统一入口、分布式数据库部署。

     目标架构

     ┌─────────────────────────────────────────────────────────────┐
     │                    API Gateway (Kong)                        │
     │                    端口: 8000                                │
     └─────────────────────────┬───────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
     ┌───▼────┐          ┌─────▼─────┐         ┌────▼─────┐
     │  Auth  │◄──gRPC──►│  Device   │◄──gRPC──►│ Firmware │
     │Service │          │  Service  │          │ Service  │
     │ :8101  │          │  :8102    │          │  :8103   │
     └───┬────┘          └─────┬─────┘          └────┬─────┘
         │                     │                     │
         │              ┌──────▼──────┐              │
         │              │ MQTT Gateway│◄─────────────┘
         │              │   :50054    │
         │              └──────┬──────┘
         │                     │
     ┌───▼────┐          ┌─────▼─────┐         ┌──────────┐
     │auth_db │          │device_db  │         │firmware_db│
     └────────┘          └───────────┘         └──────────┘

     微服务职责划分

     | 服务             | 职责                              | 数据库表                                                | 端口            
           |
     |------------------|-----------------------------------|---------------------------------------------------------|-----------------
     ------|
     | auth-service     | 用户、角色、权限、JWT认证         | users, roles, permissions, user_roles, role_permissions | HTTP:8101, 
     gRPC:50051 |
     | device-service   | 设备CRUD、设备数据、设备命令      | devices, device_data, device_commands                   | HTTP:8102, 
     gRPC:50052 |
     | firmware-service | 固件管理、升级任务、Celery Worker | firmware, firmware_upgrade_tasks                        | HTTP:8103, 
     gRPC:50053 |
     | mqtt-gateway     | MQTT消息收发、事件发布            | (无)                                                    | gRPC:50054      
           |

     服务间通信

     | 调用方           | 被调用方       | 通信方式  | 场景                   |
     |------------------|----------------|-----------|------------------------|
     | device-service   | auth-service   | gRPC      | 权限验证、用户信息查询 |
     | device-service   | mqtt-gateway   | gRPC      | 发送设备命令           |
     | firmware-service | auth-service   | gRPC      | 权限验证               |
     | firmware-service | device-service | gRPC      | 查询设备信息           |
     | firmware-service | mqtt-gateway   | gRPC      | 发送升级命令           |
     | mqtt-gateway     | device-service | Redis事件 | 设备数据/状态上报      |

     需要改造的关键文件

     | 文件                                    | 当前问题             | 改造方案                                     |
     |-----------------------------------------|----------------------|----------------------------------------------|
     | app/services/mqtt_service.py:88,104,140 | 直接调用CRUD层       | 移至mqtt-gateway，通过事件通知device-service |
     | app/api/v1/endpoints/devices.py:11,193  | 直接导入mqtt_client  | 通过gRPC调用mqtt-gateway                     |
     | app/core/dependencies.py:50-56          | 多表联查权限         | 通过gRPC调用auth-service验证                 |
     | celery_worker.py:14,92                  | 直接导入mqtt_service | 通过gRPC调用mqtt-gateway                     |

     目录结构

     wf_iot/
     ├── docker-compose.yml           # 微服务编排
     ├── kong/kong.yml                # API Gateway配置
     ├── proto/                       # gRPC定义（共享）
     │   ├── auth.proto
     │   ├── device.proto
     │   └── mqtt_gateway.proto
     ├── services/
     │   ├── auth-service/
     │   │   ├── Dockerfile
     │   │   ├── app/
     │   │   │   ├── main.py
     │   │   │   ├── api/v1/endpoints/
     │   │   │   ├── grpc/server.py
     │   │   │   ├── crud/
     │   │   │   └── db/models/
     │   │   └── alembic/
     │   ├── device-service/
     │   │   ├── app/
     │   │   │   ├── grpc/clients/auth_client.py
     │   │   │   ├── grpc/clients/mqtt_client.py
     │   │   │   └── events/subscriber.py
     │   │   └── ...
     │   ├── firmware-service/
     │   │   ├── app/tasks/firmware_tasks.py
     │   │   └── ...
     │   └── mqtt-gateway/
     │       ├── app/mqtt/handlers/
     │       ├── app/grpc/server.py
     │       └── app/events/publisher.py
     └── iot_web/                     # 前端代码

     分阶段实施计划

     阶段1: 准备工作（第1周）

     - 创建 services/ 目录结构
     - 编写 proto/auth.proto, proto/device.proto, proto/mqtt_gateway.proto
     - 生成gRPC Python代码
     - 配置Consul服务注册发现
     - 创建数据库初始化脚本 init-databases.sql

     阶段2: auth-service抽取（第2-3周）

     - 复制 app/api/v1/endpoints/auth.py, users.py, roles.py, permissions.py
     - 复制 app/crud/user.py, permission.py
     - 复制 app/db/models/user.py（含Role, Permission等）
     - 实现gRPC服务: ValidateToken, CheckPermission, GetUserById
     - 迁移数据到 iot_auth_db
     - 编写单元测试和集成测试

     阶段3: mqtt-gateway抽取（第4-5周）

     - 重构 app/services/mqtt_service.py → mqtt-gateway/app/mqtt/client.py
     - 创建消息处理器: data_handler.py, status_handler.py, command_handler.py
     - 实现Redis事件发布: device.data.received, device.status.changed
     - 实现gRPC服务: PublishMessage, SubscribeTopic
     - 移除直接CRUD调用，改为事件发布

     阶段4: device-service抽取（第6-7周）

     - 复制 app/api/v1/endpoints/devices.py
     - 复制 app/crud/device.py
     - 复制 app/db/models/device.py
     - 实现gRPC客户端: AuthGrpcClient, MqttGatewayClient
     - 实现事件订阅: 监听 device.data.received 等事件
     - 改造权限检查: 调用auth-service验证
     - 迁移数据到 iot_device_db

     阶段5: firmware-service抽取（第8-9周）

     - 复制 app/api/v1/endpoints/firmware.py
     - 复制 app/crud/firmware.py
     - 复制 app/db/models/firmware.py
     - 复制 celery_worker.py → app/tasks/firmware_tasks.py
     - 改造Celery任务: 通过gRPC调用device-service和mqtt-gateway
     - 迁移数据到 iot_firmware_db

     阶段6: API Gateway集成（第10周）

     - 配置Kong路由规则
     - 配置JWT验证插件
     - 配置限流和CORS
     - 前端API_BASE_URL指向Kong (端口8000)
     - 端到端测试

     阶段7: 清理和上线（第11周）

     - 删除旧的 iot_backend/ 单体代码
     - 更新文档 CLAUDE.md, README.md
     - 配置监控 (Prometheus + Grafana)
     - 配置日志聚合 (ELK/Loki)
     - 性能测试

     Docker Compose配置要点

     services:
       # 基础设施
       mysql_db:        # 3306, 初始化3个数据库
       redis_cache:     # 6379
       mqtt_broker:     # 1883, 8083, 18083
       consul:          # 8500

       # API Gateway
       kong:            # 8000 (proxy), 8001 (admin)

       # 微服务
       auth-service:    # 8101 (HTTP), 50051 (gRPC)
       device-service:  # 8102 (HTTP), 50052 (gRPC)
       firmware-service: # 8103 (HTTP), 50053 (gRPC)
       firmware-celery-worker:  # Celery任务处理
       mqtt-gateway:    # 50054 (gRPC)

     关键技术选型

     | 组件        | 技术选型       | 理由                      |
     |-------------|----------------|---------------------------|
     | API Gateway | Kong           | 声明式配置、JWT插件、限流 |
     | 服务间通信  | gRPC           | 高性能、强类型、双向流    |
     | 事件通信    | Redis Pub/Sub  | 已有基础设施、简单可靠    |
     | 服务发现    | Consul         | 健康检查、DNS发现         |
     | 异步任务    | Celery + Redis | 保持现有方案              |

     风险与应对

     | 风险         | 应对措施                         |
     |--------------|----------------------------------|
     | gRPC调用延迟 | Redis缓存 + 连接池 + 异步调用    |
     | 分布式事务   | Saga模式 + 最终一致性 + 幂等设计 |
     | 数据迁移风险 | 双写验证 + 回滚方案              |
     | 服务循环依赖 | 事件驱动解耦                     |

     预计工期

     总计: 11周

     - 准备工作: 1周
     - auth-service: 2周
     - mqtt-gateway: 2周
     - device-service: 2周
     - firmware-service: 2周
     - API Gateway: 1周
     - 清理上线: 1周



⏺ 计划已批准！现在开始实施微服务架构改造。让我先创建任务跟踪列表。
