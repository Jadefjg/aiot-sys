# AIoT 性能基线

这里的结果用于容量规划，不代表系统已经达到百万级生产能力。每次测试必须记录：设备数、上报周期、报文大小、QoS、TLS、峰值倍数、节点规格和结果时间。

## 1. 容量模型

```bash
python3 performance/capacity_model.py --devices 1000000 --telemetry-interval 60 --peak-factor 5
```

模型分别计算遥测、心跳、控制峰值、入口带宽、原始日/月数据量、连接内存、Broker 节点数和消费者数。`peak-factor` 只是假设，必须由故障恢复和压测数据校准。

## 2. 端到端基线

需要先启动本地服务和 MQTT Broker，再运行：

```bash
k6 run performance/k6_iot_baseline.js \
  -e BASE_URL=http://localhost:8000 \
  -e MQTT_URL=mqtt://localhost:1883 \
  -e VUS=100
```

基线覆盖 HTTP 健康检查、设备注册 API、遥测发布和控制 API。MQTT 场景需要安装 k6 的 MQTT 扩展或使用仓库现有模拟器；若环境没有扩展，先执行 HTTP 基线并记录限制。验收指标建议：HTTP 错误率 <1%、P95 <500ms、遥测端到端延迟按消息时间戳统计、无未解释 DLQ/积压增长。

设备数据接口受认证和设备权限保护；必须先取得有效 Bearer Token，并准备可写入的测试设备，否则 401/403/404 应单独归类为“测试前置失败”，不能计入容量错误率。

## 0. 隔离压测身份和设备

在后端容器或 Python 环境执行：

```bash
cd iot_backend
python scripts/seed_load_test.py --devices 100
```

脚本幂等创建 `perf-local` 测试租户、`perf_load_user` 超级用户、专用产品和设备，并输出 30 分钟短期 JWT。仅用于测试数据库；生产环境禁止使用默认密码和超级用户。将输出的 `token` 传给 k6：

```bash
k6 run performance/k6_iot_baseline.js -e TOKEN='<短期令牌>' -e DEVICE_PREFIX=perf-local -e DEVICE_COUNT=100 -e VUS=20 -e DURATION=30s
```

## 3. 分阶段测试矩阵

| 阶段 | 设备模拟 | 目标峰值 | 重点 |
|---|---:|---:|---|
| P0 | 1,000 | 100 TPS | 功能、消息幂等 |
| P1 | 10,000 | 1,000 TPS | 单 Broker、Redis/时序写入 |
| P2 | 100,000 | 10,000 TPS | Kafka/背压、规则延迟 |
| P3 | 1,000,000 | 按模型 | 集群、重连风暴、故障转移 |

每阶段至少执行稳态、突发重连、下游限速、Broker 节点故障四类测试。

## 4. MQTT 批量连接/重连模拟器

先在压测机安装依赖：

```bash
python3 -m pip install -r performance/requirements.txt
python3 performance/mqtt_reconnect.py --host 127.0.0.1 --clients 100 --rounds 3 --confirm-local
```

工具默认不会运行批量动作；`--confirm-local` 只应对测试 Broker 使用。通过 `--jitter-ms` 分散连接，逐步将其改为 0 来制造更接近风暴的场景。记录 Broker 连接数、连接失败率、重连耗时和消息丢失率。

## 5. 可控限速 Stream 消费者

```bash
python3 performance/stream_consumer.py --create-group --rate 100 --duration 60
```

将 `--rate` 设置为低于生产速率，观察 Stream 长度、pending、DLQ、端到端延迟和 Redis 内存。测试结束后恢复消费者速率，确认积压能在目标恢复窗口内清空。不要在生产 Stream 上创建未授权的消费组。

生产端示例：

```bash
python3 performance/stream_producer.py --rate 1000 --duration 60 --confirm-local
```

先让生产速率高于消费速率，记录 `group_lag`；然后停止生产并以更高 `--rate` 启动消费者，直到 `group_lag=0`，其耗时就是积压恢复时间。

当前 MQTT 模拟器每个客户端使用一个网络线程，适用于本机 100/1000 级功能和重连实验，不适合直接创建 10000 个连接。万级及以上应使用 emqtt-bench/xk6-mqtt 等事件循环工具，并分布到多台压测机，否则测到的是压测机线程上限。
