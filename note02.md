# 物联大师前端（boat-ui）业务功能与技术架构分析

> 文档基于 `src/` 与 `pages/` 源码梳理，聚焦 **Angular 管理端** 的业务组织方式与运行时机制。  
> 与 `note01.md`（全栈/后端视角）互补：本文专门说明前端如何承载 IoT 中台的管理能力。

---

## 1. 前端定位

前端工程名为 **boat-ui**（`package.json`），是物联大师的管理控制台 UI，承担：

| 职责 | 实现方式 |
|------|----------|
| 登录与权限壳 | Angular 路由守卫 + JWT/Session |
| 菜单导航 | 后端 `GET /api/menu` 动态加载 |
| 业务页面 | **服务端下发的 JS/JSON 页面 DSL**（`pages/*.js`） |
| 通用 CRUD | 调用 `/api/table/:table/*` |
| 设备实时/控制 | 调用 `/api/device/*` + WebSocket MQTT |
| 系统监控 | 调用 `/api/dash/*` |
| 模块配置 | `SettingComponent` + `/api/setting/:module` |
| 数据可视化 | ECharts、高德地图、统计卡片 |

核心设计思想：**Angular 只提供壳与模板组件，大部分业务页由 `pages/*.js` 声明式配置，无需改 TypeScript 路由即可扩展后台功能。**

---

## 2. 技术栈

| 类别 | 选型 | 说明 |
|------|------|------|
| 框架 | Angular 21 | Standalone Components，无 NgModule |
| UI | ng-zorro-antd 21 | 布局、表格、表单、Modal、通知 |
| 图表 | ECharts 6 + ngx-echarts | line/bar/pie/gauge/radar |
| 地图 | @amap/amap-jsapi-loader | 设备分布、轨迹、大屏 |
| 实时 | mqtt 5.x（自封装 MqttService） | 经 `/mqtt` WebSocket 连接内置 Broker |
| HTTP | @angular/common/http | 统一封装 SmartRequestService |
| 编辑器 | @acrodata/code-editor (CodeMirror) | 脚本/代码编辑 |
| 工具 | dayjs、xlsx、marked、ts-md5 | 时间、导入导出、Markdown、密码哈希 |
| 构建 | @angular/build:application | 产物输出到 `www/`，由 Go embed 嵌入 |

---

## 3. 总体架构

### 3.1 分层结构

```text
┌──────────────────────────────────────────────────────────────┐
│  Shell 层（固定 Angular 代码）                                  │
│  AppComponent → Router → Login / Admin / Setting / Page      │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Page 容器层 PageComponent                                    │
│  - 解析 URL → page 名称                                       │
│  - GET /api/page/{name} → 执行 JS 或解析 JSON                 │
│  - 按 template 懒加载 Template 组件                           │
│  - 支持 children / tabs / overlay 组合布局                    │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Template 层（14 种模板组件，继承 TemplateBase）               │
│  list | edit | detail | chart | statistic | amap | ...       │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Smart 组件层                                                 │
│  smart-table | smart-editor | smart-toolbar | smart-card ... │
└────────────────────────────┬─────────────────────────────────┘
                             │
              HTTP (/api/*)          MQTT (ws://host/mqtt)
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Go 后端 iot-master                                           │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```text
src/
├── main.ts                 应用入口 bootstrapApplication
├── index.html
├── styles.scss / theme.less
└── app/
    ├── app.config.ts       全局 Provider（Router/Http/MQTT/i18n）
    ├── app.routes.ts       路由与 loginGuard
    ├── app.component.*     根组件（仅 RouterOutlet）
    ├── admin/              后台布局（侧栏菜单 + Header + Outlet）
    ├── login/              登录页
    ├── password/           修改密码
    ├── setting/            系统模块配置（log/mqtt/web/broker/...）
    ├── page/               ★ 动态页面容器
    ├── template/           ★ 页面模板组件 + template.ts 类型定义
    ├── lib/                ★ 通用 Smart 组件与 Request 服务
    ├── mqtt.service.ts     WebSocket MQTT 客户端
    └── user.service.ts     用户状态

pages/                      ★ 业务页面 DSL（由 Go 服务，非 Angular 编译）
public/                     静态资源（logo、emoji 等）
www/                        ng build 产物，Go embed 或静态托管
```

---

## 4. 路由与鉴权

### 4.1 路由表（`app.routes.ts`）

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | LoginComponent | 登录 |
| `/password` | PasswordComponent | 改密 |
| `/full/**` | PageComponent | 全屏页（如数据大屏 `full/screen`） |
| `/` | AdminComponent | 需 loginGuard |
| `/page/**` | PageComponent | 业务页，路径 `/page/device` → page=`device` |
| `/setting/:module` | SettingComponent | 系统设置 |
| `**` | UnknownComponent | 404 |

**Page 路径解析规则**：`PageComponent` 取 `location.pathname.substring(6)` 作为 page 名。  
例如 `/page/device/detail` 会请求 `/api/page/device/detail`。

### 4.2 登录流程

1. 用户提交用户名 + **MD5 密码**（`LoginComponent` + `ts-md5`）
2. `POST /api/auth` → 返回 `{ token, user }`
3. `token` 存 `localStorage`，`user` 存 `UserService` + `localStorage`
4. 跳转 `/`（默认重定向 `page/dash`）

`SmartRequestService` 每次请求自动附加：

- `withCredentials: true`（Session Cookie）
- `Authorization: Bearer {token}`（JWT）

401 / token 过期 → 自动跳转 `/login`。

### 4.3 菜单与权限

`AdminComponent.loadMenu()` 请求 `GET /api/menu`（对应后端 `menu.json`）：

- **admin 用户**：完整菜单
- **非 admin**：过滤 `admin: true` 的菜单项与子项

页面内也可通过字段/按钮的 `admin: true` 控制可见性（如设备「创建」「批量删除」）。

---

## 5. 动态页面机制（核心）

### 5.1 加载流程

```text
用户访问 /page/device
    → PageComponent.load_page()
    → GET /api/page/device
    → Content-Type: application/javascript
    → new Function(jsCode)() 得到 PageContent 对象
    → load_component(content.template) 懒加载对应 Template
    → TemplateBase.build() 编译 methods 字符串为函数
    → TemplateBase.mount() 执行 mount/mounts 钩子
    → TemplateBase.load() 按 load_api / search_api 拉数
```

服务端实现见 `pkg/page/pages.go`：优先返回 `pages/{name}.js`，其次 `.json`。

### 5.2 PageContent 结构（`template/template.ts`）

页面 DSL 是 **一个 return 的对象**，常用字段：

| 字段 | 作用 |
|------|------|
| `title` / `icon` | 卡片标题与图标 |
| `template` | 模板类型：`list`/`edit`/`detail`/`chart`/... |
| `toolbar` | 工具栏表单项（SmartField + 按钮 action） |
| `fields` | 列/表单项/统计项定义 |
| `load_api` | GET 加载数据，支持 `:id` 占位符替换 |
| `search_api` | POST 列表搜索（默认 `table/{name}/search`） |
| `submit_api` | 表单提交 |
| `auto_refresh` | 秒级自动刷新 |
| `mount` / `unmount` | 生命周期钩子（字符串会被 `new Function` 编译） |
| `methods` | 自定义方法注册到组件实例 |
| `children` | 栅格子页面（nz-col span） |
| `tabs` | 标签页子页面 |
| `overlay` | 绝对定位浮层（大屏常用） |

### 5.3 子页面组合模式

**控制台**（`pages/dash.js`）：`children` 数组，每块一个 `content`。

**设备/网关详情**（`device_detail.js` / `gateway_detail.js`）：

1. 主区 `template: 'detail'` 展示基础信息
2. `load_success` 加载产品后 **动态生成 `tabs`**
3. 各 Tab 再嵌套独立 page（实时数据、日志、告警、场景…）

**数据大屏**（`pages/screen.js`）：

- 底层 `template: 'amap'` 全屏地图
- `overlay` 叠加标题、图表、统计、报警列表

### 5.4 动作系统（SmartAction）

Toolbar、表格行操作、详情字段链接统一使用 `SmartAction`：

| type | 行为 |
|------|------|
| `link` | 路由跳转，`link` 支持 `:id` 占位 |
| `page` | `router.navigate(['/page/' + page])` |
| `dialog` | Modal 打开另一个 PageComponent |
| `script` | 执行 JS 函数（`this` 指向 TemplateBase 实例） |

`TemplateBase.execute()` 统一分发；`dialog` 支持 `after_close` 回调刷新列表。

---

## 6. 模板组件（Template）

所有模板继承 **`TemplateBase`**，共享：

- `request` / `mqtt` / `modal` / `notification` / `router`
- `subscribe()` / `subscribeJSON()` MQTT 订阅
- `load()` / `load_page()` / `dialog()` / `confirm()` / `export_json()` / `import_json()`
- `dayjs` 时间工具

### 6.1 模板一览

| template | 组件 | 典型用途 |
|----------|------|----------|
| `list` | ListComponent | 设备/产品/用户/场景等列表 |
| `edit` | EditComponent | 创建/编辑表单 |
| `detail` | DetailComponent | 详情只读 + 工具栏 |
| `chart` | ChartComponent | 历史曲线、CPU/内存仪表盘 |
| `statistic` | StatisticComponent | 控制台数字统计 |
| `value` | ValueComponent | 单值大屏展示 |
| `amap` | AmapComponent | 地图、聚合、轨迹 |
| `import` / `export` | Import/ExportComponent | 表格数据导入导出 |
| `log` | LogComponent | 日志流 |
| `code` | CodeComponent | 脚本编辑 |
| `markdown` / `text` | Markdown/TextComponent | 静态说明 |
| `blank` | BlankComponent | 纯容器 |

模板通过 `PageComponent.load_component()` **动态 import()** 懒加载，减小首包体积。

### 6.2 List 模板业务逻辑

`ListComponent.load()` 构建 `ParamSearch`：

- 合并 `filter`、关键字 `$or` 模糊搜索
- 附加 `joins` 关联查询
- 优先自定义 `search()` 函数，否则 `POST search_api`

与后端 `pkg/table` 的 `filter/skip/limit/sort/joins` 协议对齐。

### 6.3 Edit / Detail 模板

- **Edit**：`SmartEditorComponent` 根据 `fields` 渲染动态表单（支持 list/table 嵌套、upload、tree-select 等）
- **Detail**：`SmartInfoComponent` 展示字段，支持 `action` 跳转关联实体

---

## 7. Smart 组件层

### 7.1 SmartRequestService

- Base URL：`/api/`
- 开发代理：`proxy.conf.json` → 远端或本地 Go 服务
- 统一错误：`NzNotificationService.error` + 401 跳转登录

### 7.2 SmartEditorComponent

声明式表单字段类型包括：`text`/`password`/`number`/`select`/`switch`/`date`/`upload`/`list`/`table`/`tree` 等，是 **产品物模型编辑**（`product_model.js`）、**场景创建** 等复杂表单的基础。

### 7.3 SmartTableComponent

- 列类型：`text`/`boolean`/`datetime`/`bytes`/`progress`/`tags`/...
- 分页、排序、筛选、批量选择
- 行内 `operators` 与 `SmartAction` 集成

### 7.4 SmartToolbarComponent

与 List/Chart 等配合，渲染 `toolbar` 字段数组，维护 `toolbar.value` 供搜索脚本读取。

### 7.5 SmartCardComponent

统一卡片外观（标题、图标、extra 刷新按钮），Admin 内页默认白底卡片；大屏可设透明/深色 `bodyStyle`。

---

## 8. MQTT 实时能力

### 8.1 连接配置

`app.config.ts`：

```typescript
provideMqtt({ url: getMqttUrl() })
// ws(s)://{host}/mqtt  与后端 Gin /mqtt WebSocket 桥接一致
```

### 8.2 使用方式

在页面 DSL 的 `mount` 或 `methods` 中：

```javascript
mount() {
  this.subscribeJSON('device/+/values', function(values) {
    // 更新 this.data
  })
}
```

`TemplateBase` 在 `ngOnDestroy` 自动 unsubscribe，避免泄漏。

### 8.3 与 HTTP 的分工

| 场景 | 通道 |
|------|------|
| 列表/CRUD/配置 | HTTP `/api/table/*`、`/api/device/*` |
| 主动采集 | HTTP `GET device/:id/sync` |
| 被动实时刷新 | MQTT 订阅 `device/{id}/values` |
| 写控制 | HTTP `POST device/:id/write` |

前端以 **HTTP 为主、MQTT 为辅**；实时数据页 `device_values.js` 默认 `auto_refresh: 10` 轮询 HTTP，也可扩展 MQTT 推送。

---

## 9. 业务功能与页面对照

### 9.1 控制台

| 菜单 | 路由 | 页面文件 | 功能 |
|------|------|----------|------|
| 控制台 | `page/dash` | `dash.js` | 在线/离线/异常设备数、产品/用户/组织统计 |
| 数据大屏 | `full/screen` | `screen.js` | 全屏地图 +  overlay 图表/报警 |
| 系统信息 | `page/system` | `system.js` | CPU/内存/磁盘/网络/线程池（admin） |

### 9.2 物联网

| 菜单 | 页面 | 核心能力 |
|------|------|----------|
| 设备管理 | `device.js` | 列表、创建/导入/导出、详情弹窗、按产品/网关过滤 |
| 报警日志 | `alarm.js` | 告警记录查询 |
| 产品库 | `product.js` | 产品 CRUD、物模型/协议配置入口 |
| 协议库 | `protocol.js` | `GET protocol/list` 展示内置协议 JSON |

**设备详情 Tab 体系**（`device_detail.js`）：

- 实时数据 `device_values`：物模型分组展示、`sync` 采集、写值
- 操作 `device_actions`：Actions 远程调用
- 历史 `device_history`：Influx 曲线
- 日志 `device_log`、告警 `alarm`、轨迹 `device_track`
- 参数 `device_settings`、网关 `device_gateway`

**网关详情 Tab 体系**（`gateway_detail.js`）在设备 Tab 基础上增加边缘侧管理：

- 子设备 `gateway_device`、内联设备 `inline`
- 场景 `scene`、串口 `serial`、网络 `socket`
- 定时 `job`、绑定 `binding`、脚本 `script`
- 桥接 `bridge`、调试 `link_debug`
- 「下载到网关」：`GET device/:id/download/:database`

### 9.3 产品配置子页

| 页面 | 功能 |
|------|------|
| `product_model.js` | 属性/事件/动作/校验器/设置 物模型编辑，支持 JSON 导入导出 |
| `product_setting_parameter.js` | 协议点位/变量 |
| `product_setting_validator.js` | 数据检查规则 |
| `product_setting_action.js` | 动作响应 |
| `product_setting_model.js` | 模型相关配置 |
| `product_device.js` | 产品下设备列表 |

### 9.4 用户与组织

| 页面 | 功能 |
|------|------|
| `group.js` / `group_detail.js` | 组织管理 |
| `user.js` / `user_create.js` | 用户管理 |
| `member.js` | 组织成员 |
| `user_log.js` | 用户操作日志 |

### 9.5 系统设置（Angular 原生页）

路由 `setting/:module`，非 pages DSL：

| module | 配置项 |
|--------|--------|
| `log` | 日志 |
| `mqtt` | MQTT 客户端 |
| `web` | Web 端口/JWT |
| `broker` | 内置 MQTT 总线 |
| `oem` | 品牌名/Logo |
| `database` | 数据库连接 |

流程：`GET setting/:module/form` 取表单定义 → `GET setting/:module` 取当前值 → `POST` 保存。

---

## 10. 典型业务链路示例

### 10.1 设备列表 → 详情 → 实时数据

```text
/page/device
  → device.js (list, POST table/device/search)
  → 点击「查看」dialog device_detail
  → load_api table/device/detail/:id
  → Tab「数据」→ device_values
  → load_api device/:id/values
  → 点击「采集」→ GET device/:id/sync → 延迟 reload values
  → 物模型来自 product/:id/setting/model
```

### 10.2 网关场景配置下发

```text
/page/device → 网关详情 gateway_detail
  → Tab scene → scene.js (filter gateway_id)
  → 创建 scene_create → table/scene/create
  → 「下载到网关」→ GET device/:gateway_id/download/scene
  → 后端 MQTT 同步至边缘
```

### 10.3 历史曲线查询

```text
device_history.js (chart line)
  → toolbar 选择时间窗/聚合方式
  → methods.load_history → GET history API
  → ChartComponent 渲染 ECharts
```

---

## 11. 构建、部署与开发

### 11.1 本地开发

```bash
npm install
npm start          # ng serve，proxy 转发 /api、/mqtt 到后端
```

后端需单独运行 `iot-master`（默认 `:8888`），或修改 `proxy.conf.json` 指向远程环境。

### 11.2 生产构建

```bash
npm run build      # 输出 www/browser/
```

Go 主程序 `//go:embed www/browser` 嵌入静态资源；`web.StaticDir` 开发时优先读磁盘。

### 11.3 Admin 壳特性

- **主题色**：12 种预设，存 `localStorage.primaryColor`，动态 `NzConfigService.set('theme')`
- **OEM**：`GET /api/oem` 覆盖侧栏标题/Logo
- **版本**：`GET /api/version` 显示在侧栏底部
- **桌面模式预留**：`switchDesktop()` 写 `ui-mode=desktop`（TODO 启动器）

---

## 12. 扩展开发指南

### 12.1 新增业务后台页（推荐路径）

1. 后端确保 `tables/xxx.json` 与 API 就绪  
2. 新增 `pages/xxx.js`：

```javascript
return {
  title: '示例',
  template: 'list',
  search_api: 'table/xxx/search',
  fields: [ /* ... */ ],
  operators: [ /* ... */ ]
}
```

3. 在 `menu.json` 增加菜单项 `{ "name": "示例", "url": "page/xxx" }`  
4. **无需修改** `app.routes.ts` 或 Angular 组件

### 12.2 新增模板类型

1. 在 `src/app/template/` 新建组件，继承 `TemplateBase`  
2. 在 `PageComponent.load_component()` 增加 `case`  
3. 在 `template.ts` 补充 Content 接口  

### 12.3 页面 DSL 最佳实践

- 复杂逻辑放 `methods`，在 `mount` 中调用  
- 列表刷新：dialog `after_close` → `this.load()`  
- URL 参数：通过 `this.params`（queryParams）传递 `id`、`gateway_id` 等  
- API 路径占位：`:id` 由 `LinkReplaceParams()` 从 params/data 替换  
- 网关维度数据：列表 `filter` 固定 `gateway_id: this.params.gateway_id`

---

## 13. 架构特点与权衡

### 13.1 优势

- **低代码扩展**：80+ 业务页均在 `pages/`，迭代快  
- **统一交互模型**：Action/Toolbar/Table 一致，学习成本低  
- **前后端解耦**：页面配置可热更新（换 `pages/*.js` 即可）  
- **单页应用体验**：Admin 壳 + 懒加载模板，体量可控  

### 13.2 注意点

- 页面 JS 通过 `new Function` 执行，**无 TypeScript 类型检查**，需规范测试  
- 安全上依赖后端鉴权；前端 `admin` 标记仅为 UI 隐藏  
- `PageComponent` 用 `pathname.substring(6)` 解析路径，需保持 `/page/` 前缀约定  
- MQTT 与 HTTP 双通道，实时页需明确选用轮询还是订阅  

---

## 14. 小结

物联大师前端是一套 **「Angular 壳 + 服务端页面 DSL + 模板组件库」** 的低代码 IoT 管理台：

1. **Shell**：Admin 布局、登录、设置、路由守卫  
2. **Page**：动态加载 `pages/*.js`，组合 children/tabs/overlay  
3. **Template**：list/edit/detail/chart/amap 等 14 类 UI 模式  
4. **Smart**：表格、表单、工具栏、HTTP/MQTT 封装  
5. **Business**：设备-产品-网关-场景-连接 全链路管理页已覆盖  

理解前端的关键是：**路由只到 `PageComponent`，真正业务在 `pages/` 与 `/api` 的协作**；读业务从 `menu.json` + 对应 `pages/*.js` 入手，读架构从 `PageComponent` → `TemplateBase` → `SmartRequestService` 入手。
