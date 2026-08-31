# Docker 容器化部署（单体）

## 架构

```text
浏览器
  │
  ▼ :80
frontend_app (Nginx)
  ├─ /iot/     → Vue SPA
  ├─ /api/     → backend_app:8000
  └─ /docs     → OpenAPI
        │
        ▼
backend_app (FastAPI) ──► mysql_db / redis_cache / mqtt_broker / influxdb
celery_worker           ──► redis_cache / mysql_db
```

## 一键启动

在仓库根目录执行（需 Docker Desktop 已运行）：

```bash
cp .env.example .env   # 首次
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs -f backend_app
```

## 访问地址

端口由 `.env` 中 `HTTP_PORT` 控制（`.env.example` 默认为 `8080`）。以下示例以 `8080` 为例：

| 服务 | URL |
|------|-----|
| 前端控制台 | http://localhost:8080/iot/ |
| API | http://localhost:8080/api/v1/ |
| Swagger | http://localhost:8080/docs |
| 健康检查 | http://localhost:8080/health |
| EMQX Dashboard | http://localhost:18083 |
| MQTT TCP | localhost:1883 |
| InfluxDB | http://localhost:8086 |

默认账号（容器启动时自动 seed）：

- `admin` / `admin123`
- `feng` / `feng123`

## 常用命令

```bash
# 重建并启动
docker compose up -d --build

# 仅基础设施
docker compose up -d mysql_db redis_cache mqtt_broker

# 停止并保留数据卷
docker compose down

# 停止并删除数据（慎用）
docker compose down -v
```

## 说明

- 根目录 `docker-compose.yml` 为推荐的全栈部署入口。
- `iot_backend/docker-compose.yml` 可用于仅启动后端相关服务（开发辅助）。
- 微服务模式见 `iot_backend/docker-compose.microservices.yml`。
