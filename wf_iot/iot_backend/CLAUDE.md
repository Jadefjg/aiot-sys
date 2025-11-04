# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **FastAPI-based IoT backend system** providing device management, user management, firmware upgrades, and MQTT communication services. The system follows a **layered architecture** with strict separation of concerns.

## Architecture

The application follows a **4-layer architecture**:

```
┌─────────────────┐
│  API Layer      │  ← FastAPI routes (app/api/v1/endpoints/)
│  (Endpoints)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ Service Layer   │  ← Business logic (app/services/)
└────────┬────────┘
         │
┌────────▼────────┐
│  CRUD Layer     │  ← Data access (app/crud/)
└────────┬────────┘
         │
┌────────▼────────┐
│  Model Layer    │  ← SQLAlchemy models (app/db/models/)
└─────────────────┘
```

**Key architectural patterns:**
- **Dependency injection** for all layer interactions
- **Pydantic models** for request/response validation (app/schemas/)
- **Session-per-request** database pattern
- **Celery** for long-running tasks (asynchronous processing)
- **MQTT service** for device communication

## Technology Stack

- **Web Framework**: FastAPI 0.104.1
- **Database**: MySQL 8.0 + SQLAlchemy 2.0.23
- **Cache/Message Broker**: Redis 5.0.1
- **Async Tasks**: Celery 5.3.4 + Redis
- **MQTT**: paho-mqtt 1.6.1
- **Authentication**: JWT (python-jose + passlib)
- **Database Migrations**: Alembic 1.12.1
- **Containerization**: Docker + Docker Compose

## Common Development Commands

### Running the Application

```bash
# Development server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Using Docker Compose (starts all services)
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

### Database Operations

```bash
# Generate migration (after model changes)
alembic revision --autogenerate -m "描述变更"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Testing

```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py test_api_users.py

# Run with coverage report
python run_tests.py --coverage

# Run tests manually
pytest test/api/test_api_users.py -v
pytest test/api/test_api_auth.py -v

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration
```

### Celery Worker

```bash
# Start Celery worker (for async tasks)
celery -A app.tasks.firmware_tasks.celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A app.tasks.firmware_tasks.celery_app beat --loglevel=info

# Monitor tasks
celery -A app.tasks.firmware_tasks.celery_app inspect active
```

### Docker Operations

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f backend_app
docker-compose logs -f celery_worker

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend_app
```

## API Structure

All API endpoints are mounted under `/api/v1/` (configurable via `settings.API_V1_STR`).

**Endpoint modules:**
- `app/api/v1/endpoints/auth.py` - Authentication & JWT
- `app/api/v1/endpoints/users.py` - User management
- `app/api/v1/endpoints/devices.py` - Device management
- `app/api/v1/endpoints/firmware.py` - Firmware upgrade management
- `app/api/v1/endpoints/roles.py` - Role-based access control
- `app/api/v1/endpoints/permissions.py` - Permission management

## Configuration

Configuration is managed through `app/core/config.py` using the `Settings` class. All settings support environment variable overrides.

**Key settings:**
- Database: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- Redis: `REDIS_HOST`, `REDIS_PORT`
- MQTT: `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`
- JWT: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Celery: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Firmware: `FIRMWARE_UPLOAD_DIR`, `FIRMWARE_BASE_URL`

## Development Guidelines

### Adding New Features

Follow this **exact order**:
1. Create SQLAlchemy model in `app/db/models/`
2. Create Pydantic schemas in `app/schemas/`
3. Implement CRUD operations in `app/crud/`
4. Implement business logic in `app/services/`
5. Create API endpoints in `app/api/v1/endpoints/`
6. Register router in `app/api/v1/api.py`
7. Create Alembic migration

### MQTT Communication

- MQTT service is initialized automatically on app startup (see `app/main.py:lifespan`)
- All MQTT operations via `app/services/mqtt_service.py`
- Topic format: `device/{device_id}/{message_type}`
- Message format: JSON
- MQTT client instance: `mqtt_client` (import from `app.services.mqtt_service`)

### Database Sessions

- Database sessions are managed per-request via dependency injection
- **Never** create global database sessions
- Always close sessions in try/finally blocks
- Use `SessionLocal()` for session creation

### Async Tasks

- Celery tasks are defined in `app/tasks/`
- Task file: `app/tasks/firmware_tasks.py`
- Primary task: `initiate_firmware_upgrade` (long-running firmware updates)
- Redis used as both broker and result backend

### Authentication Flow

1. Client sends credentials to `/api/v1/auth/login`
2. Server validates and returns JWT token
3. Client includes token in Authorization header: `Bearer {token}`
4. Protected endpoints use `get_current_user` dependency

## Critical Files

| File | Purpose |
|------|---------|
| `app/main.py` | Application entry point, lifespan management, MQTT initialization |
| `app/core/config.py` | Configuration management |
| `app/core/dependencies.py` | Common dependencies (auth, db session) |
| `app/core/security.py` | JWT token handling, password hashing |
| `app/services/mqtt_service.py` | MQTT client singleton and message handling |
| `alembic.ini` | Database migration configuration |
| `celery_worker.py` | Celery application configuration for firmware tasks |
| `docker-compose.yml` | Multi-service orchestration (MySQL, Redis, MQTT broker, app, worker) |
| `.cursorrules` | Comprehensive development guidelines (read before making changes) |

## Testing Structure

- **Unit tests**: `test/unit/` (individual functions/classes)
- **API tests**: `test/api/` (endpoint testing)
- Custom test runner: `run_tests.py` (simplifies running common test scenarios)
- Test config: `pytest.ini`

## Directory Structure (Key Paths)

```
app/
├── api/v1/              # API routes
│   ├── endpoints/       # Specific endpoint implementations
│   └── api.py           # Router aggregation
├── core/                # Core configuration & dependencies
├── crud/                # Data access layer
├── db/
│   ├── models/          # SQLAlchemy models
│   ├── session.py       # Database session management
│   └── base.py          # Base model class
├── schemas/             # Pydantic models (DTOs)
├── services/            # Business logic layer
├── tasks/               # Celery async tasks
├── utils/               # Utility functions
└── main.py              # Application entry point

test/
├── api/                 # API integration tests
├── unit/                # Unit tests
└── ...                  # Test utilities
```

## Key Implementation Details

### Device-Firmware Upgrade Flow

1. User uploads firmware via `/api/v1/firmware/upload`
2. Firmware stored in `FIRMWARE_UPLOAD_DIR`
3. Create upgrade task via `/api/v1/firmware/create-upgrade`
4. Celery task `initiate_firmware_upgrade` executes asynchronously
5. Task publishes MQTT message to device via `mqtt_service`
6. Device receives upgrade command, downloads firmware from `FIRMWARE_BASE_URL`
7. Device reports status via MQTT → status updated in database

### MQTT Message Topics

- `device/{device_id}/command` - Server to device commands
- `device/{device_id}/status` - Device status updates
- `device/{device_id}/telemetry` - Sensor data
- `device/{device_id}/firmware` - Firmware upgrade related

### Error Handling

- All API endpoints use Pydantic validation
- Authentication required for all protected routes
- Database operations wrapped in try/except blocks
- Celery task failures are logged and tracked

## Environment Setup

```bash
# Create virtual environment
python -m venv .venv
. .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (example .env)
cp .env.example .env
# Edit .env with your values
```

## Performance Considerations

- Database queries use SQLAlchemy ORM (avoid raw SQL where possible)
- Redis caching for frequently accessed data
- Connection pooling configured in `app/db/session.py`
- Async task offloading for time-consuming operations
- MQTT connection pooling (single instance via singleton pattern)

## Security Notes

- **JWT authentication** for all API endpoints
- Password hashing with **bcrypt**
- **Never commit** `.env` or other files with credentials
- All passwords/API keys must use environment variables
- CORS is enabled (configure `allow_origins` in production)
- SQL injection protection via SQLAlchemy ORM
- MQTT authentication supported (credentials via env vars)

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows (then taskkill /PID <pid> /F)
```

### Database Connection Issues
- Verify MySQL is running: `docker-compose ps mysql_db`
- Check credentials in `.env`
- Ensure migrations are applied: `alembic current`

### Celery Worker Not Processing Tasks
- Verify Redis is running
- Check worker logs: `docker-compose logs celery_worker`
- Ensure task is registered: `celery -A app.tasks.firmware_tasks.celery_app inspect registered`

### MQTT Connection Failures
- Check broker status: `docker-compose ps mqtt_broker`
- Verify MQTT credentials in `.env`
- Check broker logs: `docker-compose logs mqtt_broker`

## Development Best Practices (from .cursorrules)

- **Use Chinese comments and docstrings**
- **Follow PEP 8** with type hints
- **Layer violation is forbidden**: API → Service → CRUD → Models only
- **Use dependency injection** for all cross-layer communication
- **No direct database access** from API layer
- **Always use CRUD layer** for database operations
- **Apply Alembic migrations** for all schema changes
- **Write tests** for new functionality
- **No hardcoded secrets** in source code
- **Keep functions < 50 lines**, classes < 200 lines

## Docker Services

The `docker-compose.yml` defines these services:
- **mysql_db**: MySQL 8.0 database
- **redis_cache**: Redis for caching and message broker
- **mqtt_broker**: EMQX MQTT broker
- **backend_app**: FastAPI application
- **celery_worker**: Celery worker for async tasks
- **frontend_app**: Vue.js frontend (if present)
- **nginx**: Reverse proxy and static file server
