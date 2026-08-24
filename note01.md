# 物联大师（iot-master）业务逻辑与技术架构分析

> 文档基于仓库源码梳理，用于理解系统定位、核心业务域、运行时架构与扩展方式。  
> 项目定位：**开源物联网数据中台**（单二进制、低内存、插件化、MQTT 总线驱动）。

---

## 1. 系统定位与核心价值

物联大师不是传统「设备接入网关」的单一角色，而是一套可独立部署的 **IoT 数据中台**：

| 能力 | 说明 |
|------|------|
| 设备与产品管理 | 产品物模型、设备实例、网关/子设备、在线状态 |
| 协议与连接抽象 | 通过 MQTT 主题规范对接协议插件与连接器（serial/socket 等） |
| 实时控制与读数 | Sync / Read / Write / Action / Setting 请求-响应 |
| 规则告警 | 物模型 Validators 对实时属性做比较/表达式判定 |
| 时序历史 | 可选 InfluxDB 写入与查询 |
| 智能场景 | Scene / Job / Binding / Script（多挂在网关侧配置） |
| 管理后台 | Angular + 动态页面（`pages/*.js`）+ 通用表 CRUD |
| 插件/应用扩展 | App 包可带 menus、pages、tables、可执行文件 |

设计目标（来自 README）：

- 单一程序文件，免安装
- 极低内存占用
- 插件机制自由扩展
- 多 OS / 多架构
- Lua 扩展协议、JS 边缘计算
- 智能家居定时与联动
- WebRTC 点对点视频（能力声明，核心主链路仍是 MQTT + HTTP）

---

## 2. 总体技术架构

### 2.1 技术栈一览

| 层级 | 技术 |
|------|------|
| 后端语言 | Go 1.25 |
| HTTP | Gin（CORS / gzip / session / JWT / pprof） |
| ORM | XORM + MySQL（可配置） |
| MQTT Broker | 内置 mochi-mqtt（可关），客户端 paho |
| 时序库 | InfluxDB 2.x（可选） |
| 脚本/表达式 | gval、goja（JS） |
| 系统服务 | kardianos/service（install/uninstall） |
| 前端 | Angular 21 + ng-zorro-antd + ECharts + MQTT |
| 构建 | 前端产物嵌入 `www/browser`（`//go:embed`），亦可磁盘覆盖 |

### 2.2 逻辑分层

```text
┌─────────────────────────────────────────────────────────────┐
│  管理端 UI（Angular）                                         │
│  - 路由壳：Admin / Login / Setting / Page                     │
│  - 业务页：pages/*.js 动态加载渲染                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP /api/*  +  WebSocket MQTT
┌───────────────────────────▼─────────────────────────────────┐
│  主进程 iot-master                                            │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────┐ │
│  │ web/api │ │  table  │ │   iot    │ │ broker  │ │history│ │
│  │ 鉴权CRUD│ │ JSON表  │ │ 设备核心 │ │内置MQTT │ │Influx │ │
│  └─────────┘ └─────────┘ └────┬─────┘ └────┬────┘ └───────┘ │
│                               │            │                 │
│                         MQTT Topic Bus ◄───┘                 │
└───────────────────────────────┬─────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   连接器插件              协议插件                  边缘网关/设备
 (serial/tcp/udp...)   (modbus/dlt645/...)      (直连或经网关上报)
```

### 2.3 启动与模块依赖（boot）

入口 `main.go`：加载配置 → `boot.Startup()` → 异步 `web.Serve()` → `service.Run()`。

模块通过 `boot.Register` 声明依赖，按依赖图启动、逆序关闭。主要模块：

| 模块 | 依赖（典型） | 职责 |
|------|--------------|------|
| `config` | — | Viper 配置加载 |
| `log` | config | 日志 |
| `database` | config/log | XORM / MySQL |
| `web` | config | Gin Engine、静态资源、端口 |
| `mqtt` | — | MQTT 客户端连接（可连内置 broker） |
| `broker` | web/log/database | 内置 MQTT Server + `/mqtt` WS |
| `table` | config/database/apps | 扫描 `tables/*.json`、同步表结构 |
| `api` | web/log/database | 注册 `/api` 路由 |
| `iot` | log/mqtt/database/table | 设备 MQTT 订阅、协议列扩展 |
| `influxdb` | — | 历史写入（可禁用） |
| `cron` / `pool` / `debug` / `weixin` / `oem` | 各自依赖 | 定时、协程池、调试、微信、OEM |

---

## 3. 核心业务域

### 3.1 产品（Product）与物模型（Model）

**产品**是设备类型模板，描述能力与协议：

- 基础：名称、类型、协议、版本、图片
- 能力开关：`gateway` / `smart` / `controllable` / `writable` / `programmable` / `configurable` / `ota` / `locatable`

**物模型**（`product_model` / `pkg/product`）定义：

- **Properties**：属性点（name/label/unit/type/mode/precision）
- **Events**：事件及参数
- **Actions**：远程操作（button/switch/slider 等）
- **Validators**：告警规则（比较或表达式）
- **Settings**：可下发配置表单字段

产品协议相关配置存在 `product_config`，并可通过 MQTT `product/{product_id}/config/{name}`、`product/{product_id}/model` 同步给插件/网关。

### 3.2 设备（Device）生命周期

设备实例字段要点：

- 归属：`tenant_id` / `group_id`
- 层级：`gateway_id`（子设备挂网关）、`product_id`、`link_id`
- 状态：`online` / `error` / `error_string` / `disabled`
- 位置：`longitude` / `latitude` / `geo_code`（geohash）

**内存态**：`devices` 为进程内 `Map[Device]`。首次 MQTT 活动或 API 访问时 `LoadDevice` 从 DB 加载并缓存；离线约 1 分钟后清理缓存。

**关键业务流：**

1. **注册** `device/{id}/register`  
   - 不存在则按 product 自动建档并上线  
   - 可携带 settings / models / databases 版本信息，触发云端→设备同步，必要时延迟 reboot
2. **上报属性** `device/{id}/values` 或 `.../property`  
   - 更新内存值 → Validators 评估告警 → 写 InfluxDB → 必要时刷新 online
3. **上下线** `online` / `offline` / Broker `$events/client_disconnected`  
   - 写 DB；网关离线时子设备一并 offline；写 `device_log`
4. **定位** `device/{id}/location` → 更新坐标与轨迹表
5. **故障** `device/{id}/error` → 标记错误并插入 Alarm

**远程控制（HTTP → MQTT 请求-响应）：**

| API | MQTT | 说明 |
|-----|------|------|
| `GET device/:id/sync` | `.../sync` + `.../sync/response` | 全量同步 |
| `GET device/:id/read` | `.../read` | 按点读取 |
| `POST device/:id/write` | `.../write` | 写属性 |
| `POST device/:id/action/:action` | `.../action` | 执行动作 |
| `POST device/:id/setting/:name` | `.../setting` | 下发配置 |

子设备路径支持 `.../:child`；若设备有 `gateway_id`，请求发往网关主题，`device_id` 指向子设备。响应通过 `msg_id` 与内存 channel 匹配，默认超时约 30s。

### 3.3 告警（Alarm / Validator）

设备 `PutValues` 时对物模型中的 Validators 逐条评估：

- **compare**：字段与阈值的 =/!=/>/>=/</<=  
- **expression**：gval 表达式  
- 支持 **Delay**（持续满足才告）、**Reset / ResetTimes**（重复告警节流）  
- 告警入库并发布 `device/{id}/alarm`  
- 标题/消息支持 `{field}` 占位替换

### 3.4 连接与协议（Link / Protocol）

协议元数据在 `protocols/*.json`（如 Modbus），定义：

- `device_extend_columns`：启动时动态 ALTER `device` / `inline` 表（如 `slave`）
- `device_extend_fields` / `point_extend_fields` / `option_fields`：前端表单扩展

连接侧数据表：

- **serial**：串口连接（挂 `gateway_id`）
- **socket**：网络连接
- **inline**：网关内联子设备映射（product/link）
- **bridge**：连接桥接（link1 ↔ link2）

运行时协议插件与连接器通过 MQTT 协作（见第 4 节），主进程本身不内嵌完整协议编解码，而是做 **主题编排 + 产品/设备状态中枢**。

### 3.5 智能家居相关配置（多绑定网关）

以下表多以 `(id, gateway_id)` 为联合主键，配置下发/同步到边缘网关执行：

| 表 | 业务含义 |
|----|----------|
| `scene` | 场景：时间范围、星期、triggers、conditions、actions、延迟 |
| `job` | 定时任务：time/weekdays/action/data/单次 |
| `binding` | 设备联动绑定（device1 ↔ device2，双向开关） |
| `script` | JS 脚本（内容、间隔、延迟、重复） |
| `member` | 成员（组织/用户侧扩展） |

README 中的「定时和联动控制」主要体现在这些边缘侧可执行配置，而非全部在云端 gocron 硬编码。

### 3.6 组织与用户

- **group**：组织树/分组，设备可挂 `group_id`
- **user / password / user_log**：账号与 MD5 密码；首次 `admin` 自动创建（默认密码 `123456` 的 MD5）
- **tenant_id**：配置项 `tenant: true`，多租户字段已在表结构预留
- 鉴权：Session + JWT（`web.jwt_*`）；微信小程序模块可选（PowerWeChat）

### 3.7 历史与大屏

- `history`：InfluxDB WriteAPI 异步写点；measurement≈product_id，tag≈device_id
- 前端：控制台 `page/dash`、全屏大屏 `full/screen`、设备历史页 `device_history`

---

## 4. MQTT 总线规范（插件互操作核心）

插件与主程序 **主要通过 MQTT 主题解耦**，形成「连接层 → 协议层 → 设备层」流水线。

### 4.1 连接消息 `link/{linker}/{link_id}/#`

| 动作 | 主题后缀 | 载荷 |
|------|----------|------|
| 打开 | open | JSON（含 remote 等） |
| 关闭 | close | — |
| 上行原始 | up | 二进制 |
| 下行原始 | down | 二进制 |

`linker` 示例：serial、tcp-client、tcp-server、udp-*、gnet-server 等。

### 4.2 协议消息 `protocol/{protocol}/{linker}/{link_id}/#`

| 动作 | 说明 |
|------|------|
| open/close | 绑定设备列表到连接 |
| up | 原始数据定向到协议插件 |
| poll / sync / read / write / action | 轮询与读写操作（带 msg_id） |

协议侧下行仍走 `link/.../down`。产品变更约定为「先删后加」。

### 4.3 设备消息 `device/{device_id}/#`

属性上报、读写、事件、动作及对应 `*/response`；另有 register / online / offline / location / error / log / alarm / setting 等扩展主题（实现见 `iot/device-mqtt.go`）。

### 4.4 产品 / 项目 / 空间

- `product/{id}/model`、`product/{id}/config/{name}`
- `project/{project_id}/{device_id}/...`、`space/{space_id}/{device_id}/...`：属性与事件投影（规范层）
- `push/{device_id}/values`：异常/推送类消息

### 4.5 内置 Broker 特点

- TCP `:port`（默认 1883）+ Gin `/mqtt` WebSocket
- 支持匿名或 Hook Key 鉴权
- 可选 Unix Socket
- 进程内通过虚拟双端连接（VConn）挂载「internal」客户端，避免回环网络开销

---

## 5. 数据与 API 架构

### 5.1 表驱动（Table Engine）

`tables/*.json` 声明表名、字段、索引、joins。启动时：

1. `Scan` 加载定义  
2. `Init` 编译钩子  
3. 若 `table.sync=true` 则同步物理表结构  

通用 REST（均在 `/api` 下）：

```text
POST   table/:table/search|count|group|create|import|export
PUT    table/:table/create
POST   table/:table/update/*id
GET|DELETE table/:table/delete/*id
GET    table/:table/detail/*id | query/*id
```

业务扩展 API 在 `iot/*-api.go`、`apis/*`、`history`、`weixin` 等包的 `init()` 中 `api.Register`。

### 5.2 动态页面（Page DSL）

- 服务端：`GET /api/page/*page` 返回 `pages/{page}.js` 或 `.json`
- 前端：`PageComponent` 按路径加载页面描述，用模板组件（表格、表单、卡片、图表等）渲染
- 效果：多数业务页 **无需改 Angular 路由**，增删 `pages/*.js` + `tables/*.json` 即可扩展后台

### 5.3 配置文件（示意）

核心配置段（见 `iot-master.yaml.bak`）：

- `web`：端口、JWT、gzip、TLS
- `database`：MySQL URL、sync
- `mqtt` / `broker`：客户端与内置总线
- `influxdb`：历史库
- `table.path`：表定义目录
- `oem` / `weixin` / `pool` / `log` / `service`

---

## 6. 前端架构要点

- 工程名 `boat-ui`，Angular standalone 组件 + ng-zorro
- 路由：登录守卫 → `AdminComponent` 子路由 `page/**`、`setting/:module`
- `MqttService`：浏览器侧订阅设备实时主题
- 菜单：`menu.json` 嵌入/加载（控制台、物联网、用户、系统设置）
- 构建产物放入 `www/browser`，由 Go embed；开发时 `StaticDir` 优先读磁盘避免旧嵌入资源 404

---

## 7. 典型端到端数据流

### 7.1 属性上报与告警

```text
设备/网关 ──MQTT──► device/{id}/values
                 │
                 ▼
            LoadDevice / 缓存
                 │
                 ▼
            PutValues：内存更新
                 ├─ Validators → Alarm DB + device/{id}/alarm
                 └─ history.Write → InfluxDB
```

### 7.2 平台写点

```text
浏览器 ──HTTP──► POST /api/device/:id/write
                 │
                 ▼
            Device.Write → MQTT device/{id|gateway}/write
                 │
         协议插件/网关执行
                 │
                 ▼
            .../write/response (msg_id) → 解除 wait → HTTP 返回
```

### 7.3 串口 Modbus 类采集（插件协作示意）

```text
连接器插件 link/.../up ──► 协议插件 protocol/modbus/.../up
                              │ 解析寄存器
                              ▼
                         device/{id}/values ──► 中台
中台 write/read ──► protocol/.../write|read ──► link/.../down ──► 现场总线
```

---

## 8. 目录结构速查

```text
main.go                 入口、embed 前端、注册 service
apis/                   登录鉴权、备份、仪表盘、设置等
iot/                    设备/产品/协议业务核心
history/                InfluxDB 历史
weixin/                 微信小程序
tables/                 表结构 JSON
pages/                  后台页面 DSL（JS）
protocols/              协议元数据 JSON
pkg/
  boot/                 依赖启动框架
  web/ api/             HTTP 与路由注册
  table/                通用 CRUD 引擎
  broker/ mqtt/         MQTT 服务与客户端
  product/ protocol/    物模型与协议结构
  db/ config/ log/      基础设施
  app/                  应用/插件包模型
  javascript/ calc/     脚本与表达式
  oem/ smart/ cron/...  OEM、表单字段、定时等
src/                    Angular 源码
www/                    前端构建产物
plc/st/                 PLC ST 相关（解析等，扩展方向）
```

---

## 9. 扩展与二次开发指引

| 目标 | 做法 |
|------|------|
| 加业务表与后台列表 | 新增 `tables/x.json` + `pages/x.js`，重启同步表 |
| 加设备侧 API | 在 `iot` 或 `apis` 的 `init` 中 `api.Register` |
| 加协议类型 | 增加 `protocols/{name}.json`（扩展列/表单字段）；另实现协议插件订阅对应 MQTT |
| 加连接器 | 独立插件实现 `link/{linker}/...` 约定 |
| 加启动模块 | `boot.Register` + 声明 `Depends` |
| 加应用包 | 按 `pkg/app.App` 打包 menus/pages/tables/executable |
| 定制菜单/OEM | `menu.json`、`oem` 配置 |

---

## 10. 当前边界与待办（结合 TODO / 源码）

- 前端：应用管理（列表/安装/证书）、启动器等仍在规划
- 后端：应用管理、数据总线能力持续完善
- 协议库：Modbus RTU/TCP、部分 PLC、DL/T645、CJ/T188 已支持；BACnet、KNX、IEC104/61850、更多水利规约等未完成或未合入本仓库
- 主进程侧重 **中台编排**；完整链路通常还需配套连接器/协议插件与边缘网关进程

---

## 11. 小结

物联大师的架构可以概括为：

1. **以 MQTT 主题规范为总线契约**，连接器、协议插件、设备/网关、中台解耦协作；  
2. **以产品物模型为语义中心**，设备实例承载状态、控制与告警；  
3. **以 Table + Page 元数据驱动管理后台**，降低 CRUD 与表单开发成本；  
4. **以 boot 模块化单进程** 聚合 Web、Broker、DB、历史库，兼顾「单文件部署」与可扩展插件生态。

理解业务时优先抓住三条主线：**产品/设备模型 → MQTT 上下行 → 表驱动管理台**；理解技术时优先抓住：**boot 依赖图 + Gin API + 内置/外置 MQTT + XORM/Influx**。
`)