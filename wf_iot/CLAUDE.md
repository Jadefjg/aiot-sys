# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack **IoT Device Management System** with dual deployment modes:
- **Monolithic**: FastAPI backend + Vue 3 frontend
- **Microservices**: 4 independent services with Kong API Gateway

```
wf_iot/
├── iot_backend/     # 后端代码 (FastAPI + 微服务)
├── iot_web/         # 前端代码 (Vue 3)
└── CLAUDE.md        # 项目文档
```

Infrastructure: MySQL 8.0, Redis, EMQX (MQTT broker), Docker Compose

## Commands

### Backend Development (Monolithic)
```bash
cd iot_backend

# Dev server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Testing
python run_tests.py                              # All tests
python run_tests.py test_api_users.py            # Single file
pytest test/api/test_api_users.py::TestUserAPI::test_create_user_success -v  # Single test
pytest -m unit                                   # Unit tests only
pytest --cov=app --cov-report=html               # Coverage report

# Database migrations
alembic revision --autogenerate -m "描述变更"
alembic upgrade head

# Celery worker (firmware upgrades)
celery -A app.tasks.firmware_tasks.celery_app worker --loglevel=info
```

### Docker (Monolithic)
```bash
cd iot_backend
docker-compose up -d --build
docker-compose logs -f backend_app
docker-compose down
```

### Microservices
```bash
cd iot_backend

# Start all microservices
./scripts/start-microservices.sh
# or: docker-compose -f docker-compose.microservices.yml up -d --build

# Stop
./scripts/stop-microservices.sh

# Logs
docker-compose -f docker-compose.microservices.yml logs -f auth-service

# Generate gRPC code
cd proto && ./generate.sh
```

### Frontend
```bash
cd iot_web
npm install
npm run dev    # Port 5173 (Vite)
```

## Architecture

### Backend 4-Layer Architecture (strict separation)
```
API Layer (app/api/v1/endpoints/)     → FastAPI routes
         ↓
Service Layer (app/services/)          → Business logic
         ↓
CRUD Layer (app/crud/)                 → Data access
         ↓
Model Layer (app/db/models/)           → SQLAlchemy ORM
```

**Layer violation forbidden**: API → Service → CRUD → Models only. Use dependency injection for cross-layer communication.

### Microservices Architecture
```
Kong API Gateway (:8000)
        │
        ├── Auth Service (:8101/50051 gRPC) → MySQL :3307
        ├── Device Service (:8102/50052 gRPC) → MySQL :3308
        ├── Firmware Service (:8103/50053 gRPC) → MySQL :3309
        └── MQTT Gateway (:50054 gRPC) → EMQX :1883
```

Communication: gRPC for sync calls, Redis Pub/Sub for async events (`iot:device:status`, `iot:device:data`, `iot:firmware:upgrade`)

### Adding Backend Features
1. SQLAlchemy model in `app/db/models/`
2. Pydantic schemas in `app/schemas/`
3. CRUD operations in `app/crud/`
4. Business logic in `app/services/`
5. API endpoint in `app/api/v1/endpoints/`
6. Register router in `app/api/v1/api.py`
7. Alembic migration

## API Endpoints

All under `/api/v1/`: `/auth`, `/users`, `/devices`, `/firmware`, `/roles`, `/permissions`, `/health`

## MQTT

- Service: `iot_backend/app/services/mqtt_service.py` (singleton)
- Topics: `device/{device_id}/{message_type}` (data, status, command, firmware, heartbeat)

## Configuration

Environment variables via `iot_backend/app/core/config.py`:
- Database: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- Redis: `REDIS_HOST`, `REDIS_PORT`
- MQTT: `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`
- JWT: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

## Development Guidelines

**From .cursorrules:**
- Chinese comments and docstrings
- PEP 8 with type hints
- Code limits: functions < 50 lines, classes < 200 lines, files < 300 lines
- All database operations through CRUD layer
- Commit format: `类型: 简短描述`
- Branch naming: `feature/功能名`, `bugfix/问题描述`, `hotfix/紧急修复`

**Frontend known issues (from iot_web/.cursorrules):**
- Login.vue: `from`→`form`, `sumbit`→`submit`
- DevicesManagement.vue: inconsistent function names (`addDevices` vs `addDevice`), missing parameters

## Critical Files

| Path | Purpose |
|------|---------|
| `iot_backend/app/main.py` | Entry point, lifespan, protocol init |
| `iot_backend/app/core/config.py` | Settings management |
| `iot_backend/app/core/dependencies.py` | Auth/DB injection |
| `iot_backend/app/services/mqtt_service.py` | MQTT singleton |
| `iot_backend/app/api/v1/api.py` | Router aggregation |
| `iot_backend/proto/*.proto` | gRPC service definitions |
| `iot_backend/services/` | Microservices code |
| `iot_backend/docker-compose.microservices.yml` | Microservices orchestration |

## Docker Services (Monolithic)

- `mysql_db` (3306) - MySQL
- `redis_cache` (6379) - Redis
- `mqtt_broker` (1883, 8083 WS, 8080 dashboard) - EMQX
- `backend_app` (8000) - FastAPI
- `celery_worker` - Async tasks
- `frontend_app` / `nginx` - Vue SPA

## Troubleshooting

```bash
lsof -ti:8000 | xargs kill -9              # Kill port 8000
curl http://localhost:8000/health          # Health check
alembic current                            # Check migrations
celery -A app.tasks.firmware_tasks.celery_app inspect registered  # Verify Celery
```
