# AIOT-SYS 架构分析

> 全栈物联网平台：在设备管理 / OTA / RBAC 之上，叠加产品物模型、MQTT 属性总线、校验告警与远程控制，形成轻量数据中台形态。  
> 文档基于当前仓库实现梳理（FastAPI + Vue），业务对标 `note01.md`（iot-master）核心主线。

---

## 1. 系统定位

| 维度 | 说明 |
|------|------|
| 部署形态 | **双模式**：单体 + 微服务 |
| 后端分层 | **4 层**：API → Service → CRUD → Model |
| 已落地业务域 | 6+（认证、产品、设备、控制、告警、OTA 等） |
| 相对完整中台缺口 | 约 5 项（协议插件总线、时序库、场景执行引擎等） |

**定位一句话**：不是纯设备接入网关，而是以「产品物模型为语义中心、MQTT 为主干总线、管理台为控制面」的 IoT 数据中台切片。

理解系统时抓住三条主线：

1. **产品 / 设备模型**
2. **MQTT 上下行**
3. **管理台控制面**

> 中台能力主要落在单体 `iot_backend/app/` 树；微服务拆分覆盖认证、设备、固件与 MQTT 网关，但物模型 / 告警 / 场景等新域以单体实现为主。

---

## 2. 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | Python · FastAPI · SQLAlchemy · Alembic · JWT · Celery |
| 前端 | Vue 3 · Vite · Pinia · Vue Router · Element Plus · Axios |
| 基础设施 | MySQL 8 · Redis · EMQX · Docker Compose |
| 微服务 | Kong · auth / device / firmware / mqtt-gateway · gRPC + Redis 事件 |

### 微服务端口（参考）

| 服务 | HTTP | gRPC | 数据 |
|------|------|------|------|
| auth-service | 8101 | 50051 | MySQL :3307 |
| device-service | 8102 | 50052 | MySQL :3308 |
| firmware-service | 8103 | 50053 | MySQL :3309 |
| mqtt-gateway | — | 50054 | EMQX :1883 |
| Kong | 8000（代理） / 8001（管理） | — | — |

---

## 3. 逻辑分层

```text
┌─────────────────────────────────────────────┐
│  管理端 Vue（/iot/）                          │
│  HTTP /api/v1  +  MQTT（经 Broker）           │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│  FastAPI 单体（或 Kong → 微服务）             │
│  API → Service → CRUD → Models              │
│  枢纽：mqtt_service / device_runtime /      │
│        validator_service                    │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     MySQL 8         Redis          EMQX
```

| 模式 | 说明 |
|------|------|
| 单体 | FastAPI `:8000` + Celery + 共享 MySQL / Redis / EMQX |
| 微服务 | Kong `:8000` → auth / device / firmware；mqtt-gateway 经 gRPC |
| 总线 | EMQX MQTT；微服务侧另有 Redis Pub/Sub 事件 |

### 后端目录对应

| 层 | 路径 |
|----|------|
| API | `iot_backend/app/api/v1/endpoints/` |
| Service | `iot_backend/app/services/` |
| CRUD | `iot_backend/app/crud/` |
| Models | `iot_backend/app/db/models/` |
| Schemas | `iot_backend/app/schemas/` |
| 路由聚合 | `iot_backend/app/api/v1/api.py` |

---

## 4. 业务域成熟度

| 业务域 | 状态 | 能力要点 |
|--------|------|----------|
| 认证 / RBAC | 成熟 | JWT 登录、用户/角色/权限 CRUD、资源动作授权 |
| 产品 / 物模型 | 已实现 | 产品模板、属性/事件/动作/Validators/Settings、能力开关 |
| 设备生命周期 | 已实现 | 注册建档、上下线、网关/子设备、属性快照、定位/故障 |
| 远程控制 | 已实现 | sync / read / write / action / setting，`msg_id` 请求-响应 |
| 告警 | 已实现 | 物模型规则评估、入库、MQTT 推送、确认 |
| 固件 OTA | 成熟 | 固件版本、升级任务、Celery 异步执行 |
| 智能场景 | 部分 | Scene/Job CRUD；Binding/Script 仅模型；无执行引擎 |
| 分组 | 已实现 | DeviceGroup API + `device.group_id`；前端无独立页 |
| 历史数据 | 部分 | MySQL `device_data`；无 Influx 时序层 |
| 连接 / 协议插件 | 部分 | MQTT 主链路；CoAP/AMQP 适配骨架；无 link/protocol 总线 |

---

## 5. 典型端到端数据流

### 5.1 属性上报 → 告警

```text
设备 MQTT → device/{id}/values|property|data
         → put_values 合并快照并写 DeviceData
         → Validators 评估 → Alarm 入库
         → 发布 device/{id}/alarm
```

### 5.2 平台写点

```text
UI/API POST /devices/{id}/write
         → MQTT write（含 msg_id；可路由到网关主题）
         → 设备 .../write/response
         → 解除等待 → HTTP 返回（默认超时 30s）
```

---

## 6. API 面（`/api/v1`）

| 前缀 | 职责 |
|------|------|
| `/auth` `/users` `/roles` `/permissions` | 身份与 RBAC |
| `/products` | 产品与物模型 |
| `/devices`（含 register / values / sync / read / write / action / setting） | 设备与远程控制 |
| `/alarms` `/groups` `/scenes` `/jobs` | 告警、分组、场景配置 |
| `/firmware` | 固件与 OTA 任务 |
| `/` `/health` | 根与健康检查 |

前端基路径：`/iot/`，API 代理基地址通常为 `/iot/api/v1`。

---

## 7. MQTT 主题契约（主干）

### 上行（设备 → 平台）

| 主题后缀 | 含义 |
|----------|------|
| `values` / `property` / `data` | 属性 / 遥测上报 |
| `register` | 注册 / 自动建档 |
| `online` / `offline` / `heartbeat` / `status` | 在线状态 |
| `location` | 定位 |
| `error` | 故障 |
| `*/response` | 控制请求响应（含 `msg_id`） |
| `firmware/status` | OTA 状态 |

### 下行（平台 → 设备）

| 主题后缀 | 含义 |
|----------|------|
| `sync` / `read` / `write` / `action` / `setting` | 远程控制 |
| `command` | 兼容旧命令路径 |
| `alarm` | 规则触发后回写总线 |

说明：子设备控制可改写到网关主题（`device/{gateway_id}/...`，载荷中带 `device_id`）。

---

## 8. 相对完整中台的主要缺口

| 缺口 | 说明 |
|------|------|
| 连接器 / 协议插件总线 | 缺少 `link/...` 与 `protocol/modbus/...` 主题编排，无法像 iot-master 解耦串口/TCP/Modbus |
| 时序历史 | 仅 MySQL `DeviceData`，无 Influx 等 measurement/tag 查询层 |
| 场景执行引擎 | Scene/Job 多为配置镜像；Binding/Script 缺 API；边缘侧未落地 |
| 产品 MQTT 同步 | 物模型变更可写库，产品 config/model 主题契约未完整对齐插件生态 |
| 插件化扩展 | 无 App 包、Table/Page DSL、内置 Broker、Lua/JS 边缘运行时 |

---

## 9. 关键文件

| 路径 | 用途 |
|------|------|
| `iot_backend/app/main.py` | 入口、lifespan、协议启动 |
| `iot_backend/app/api/v1/api.py` | 路由聚合 |
| `iot_backend/app/services/mqtt_service.py` | MQTT 订阅与分发 |
| `iot_backend/app/services/device_runtime_service.py` | 设备运行时 / 请求-响应 |
| `iot_backend/app/services/validator_service.py` | 物模型告警评估 |
| `iot_backend/app/db/models/product.py` | 产品与物模型 |
| `iot_backend/app/db/models/device.py` | 设备实例 |
| `iot_backend/app/db/models/smart.py` | 场景 / 定时 / 绑定 / 脚本 |
| `iot_backend/docker-compose.yml` | 单体编排 |
| `iot_backend/docker-compose.microservices.yml` | 微服务编排 |
| `iot_web/src/router/index.js` | 前端路由 |
| `note01.md` | iot-master 业务参考（技术栈不同） |

---

## 10. 小结

AIOT-SYS 当前形态可概括为：

1. **以 MQTT 主题为设备侧契约**，承载注册、属性、状态与远程控制；  
2. **以产品物模型为语义中心**，设备实例承载状态、控制与告警；  
3. **以 Vue 管理台为控制面**，覆盖产品、设备详情、告警与场景配置；  
4. **以 FastAPI 四层单体为主实现中台能力**，并保留 Kong 微服务拆分路径。

与 `note01.md` 中的 iot-master 相比：核心「模型 → MQTT → 管理台」主线已落地；协议插件总线、时序库、场景真正执行与插件生态仍是后续扩展方向。
