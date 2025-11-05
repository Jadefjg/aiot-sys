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
- **Multi-protocol support** - Pluggable protocol services (MQTT currently implemented, extensible for CoAP, Bluetooth, Zigbee, LoRa, etc.)
- **Protocol abstraction layer** - Unified device communication interface

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
# Run all tests (user and auth modules)
python run_tests.py

# Run specific test file
python run_tests.py test_api_users.py

# Run with coverage report
python run_tests.py --coverage

# Run tests manually with test markers
pytest test/api/test_api_users.py -v
pytest test/api/test_api_auth.py -v
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run all API tests
pytest test/api/ -v

# Run with coverage and HTML report
pytest --cov=app --cov-report=html --cov-report=term-missing -v
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

## IoT Protocol Support

### Currently Supported Protocols

- **MQTT** - Fully implemented via `app/services/mqtt_service.py`
  - Supports device data telemetry, status updates, command/control, firmware upgrades
  - Topic format: `device/{device_id}/{message_type}`
  - Message format: JSON
  - Real-time bi-directional communication

### Protocol Extension Guide

The system is designed to support multiple IoT protocols. To add a new protocol:

1. **Create Protocol Service** (e.g., `app/services/coap_service.py`)
   ```python
   class CoAPService:
       def __init__(self):
           # Initialize protocol-specific client

       def handle_message(self, device_id: str, data: dict):
           # Process incoming message

       def send_command(self, device_id: str, command: dict):
           # Send command to device
   ```

2. **Update Device Model**
   - Use existing `device_metadata` field in `Device` model to store protocol-specific info
   - Protocol configuration stored as JSON: `{"protocol": "coap", "endpoint": "coap://...", "credentials": {...}}`

3. **Protocol-Specific Message Handling**
   - Each protocol has its own message format and transport mechanism
   - Standardize data to JSON format before storing in `DeviceData` table
   - Use `data_type` field to identify protocol source

4. **Register Service in App Startup**
   - Initialize protocol service in `app/main.py` lifespan
   - Add to service registry for dependency injection

5. **Create Protocol Registry** (Recommended)
   ```python
   # app/services/protocol_registry.py
   class ProtocolRegistry:
       _services = {}

       @classmethod
       def register(cls, protocol_name: str, service):
           cls._services[protocol_name] = service

       @classmethod
       def get_service(cls, protocol_name: str):
           return cls._services.get(protocol_name)

       @classmethod
       def send_command(cls, device_metadata: dict, command: dict):
           protocol = device_metadata.get("protocol")
           service = cls.get_service(protocol)
           if service:
               device_id = device_metadata.get("device_id")
               return service.send_command(device_id, command)
           raise ValueError(f"Unsupported protocol: {protocol}")
   ```

### Device Configuration for Multi-Protocol

Devices store protocol configuration in `device_metadata` field:

```json
{
  "protocol": "mqtt",
  "endpoint": "mqtt://broker.example.com:1883",
  "topics": {
    "data": "device/{device_id}/data",
    "status": "device/{device_id}/status",
    "command": "device/{device_id}/command"
  },
  "credentials": {
    "username": "device_user",
    "password": "encrypted_password"
  },
  "options": {
    "qos": 1,
    "retain": false
  }
}
```

For other protocols:
- **CoAP**: `{"protocol": "coap", "endpoint": "coap://device.local", "resources": {...}}`
- **HTTP**: `{"protocol": "http", "endpoint": "http://api.device.com", "api_key": "..."}`
- **Bluetooth**: `{"protocol": "ble", "mac_address": "XX:XX:XX:XX:XX:XX", "services": [...]}`

### Message Routing

Each protocol service handles its own message format but normalizes to common format:

```python
# Standardized message format in DeviceData
{
  "device_id": "device_123",
  "timestamp": "2024-01-01T00:00:00Z",
  "protocol": "mqtt",  # Original protocol
  "data_type": "telemetry",
  "data": {  # Actual sensor data
    "temperature": 25.5,
    "humidity": 60
  },
  "quality": "good",
  "raw_message": {...}  # Original protocol message if needed
}

### Protocol Selection Matrix

| Scenario | Recommended Protocol | Reason |
|----------|---------------------|--------|
| **Battery-powered sensors** | LoRa, Zigbee, BLE | Ultra-low power consumption |
| **Real-time control** | MQTT, WebSocket | Low latency, persistent connection |
| **Smart home automation** | Zigbee, Z-Wave, Thread, Matter | Mesh networking, reliability |
| **Industrial IoT** | MQTT, AMQP, OPC-UA | Enterprise-grade, reliability |
| **Wearable devices** | Bluetooth LE | Low energy, short range |
| **Long-range telemetry** | LoRaWAN, NB-IoT | km-range coverage |
| **High-throughput data** | MQTT, HTTP, WebSocket | Efficient data transfer |
| **Constrained devices** | CoAP, MQTT (lightweight) | Minimal resource usage |
| **Building automation** | BACnet, Zigbee, Thread | Industry standard |
| **Cross-vendor interoperability** | Matter, MQTT | Open standards |

### Protocol Use Cases

| Protocol | Best For | Characteristics |
|----------|----------|-----------------|
| **MQTT** | General IoT, real-time telemetry | Lightweight, pub-sub, QoS support |
| **CoAP** | Constrained devices, RESTful IoT | UDP-based, low power |
| **HTTP/HTTPS** | Cloud-connected devices | Standard web protocols |
| **WebSocket** | Real-time dashboard updates | Persistent bi-directional |
| **Bluetooth/BLE** | Proximity devices, wearables | Short-range, low energy |
| **Zigbee** | Home automation, mesh networks | Low power, self-healing mesh |
| **Z-Wave** | Smart home devices | Sub-GHz, reliable mesh |
| **LoRa/LoRaWAN** | Long-range, low-bandwidth | km-range, ultra-low power |
| **Thread** | Smart home, IP-based | IPv6, mesh, Matter-ready |
| **Matter** | Smart home interoperability | Unified standard for IoT |
| **AMQP** | Enterprise messaging | Reliable message delivery |

### Protocol Abstraction

The system uses a **unified device communication interface**:

```python
# Common interface all protocols should implement
class ProtocolService:
    def connect_device(self, device: Device) -> bool:
        """Establish connection with device"""
        pass

    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect device"""
        pass

    def send_command(self, device_id: str, command: dict) -> bool:
        """Send command to device"""
        pass

    def handle_message(self, device_id: str, data: dict):
        """Handle incoming message from device"""
        # Normalize data and store in database
        pass
```

### Service Initialization (Current Implementation)

Services are initialized in `app/main.py:lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start all protocol services
    mqtt_service.start()  # MQTT service
    # coap_service.start()  # Future: CoAP service
    # ble_service.start()   # Future: Bluetooth service

    yield

    # Stop all protocol services
    mqtt_service.stop()
    # coap_service.stop()
    # ble_service.stop()
```

Health check endpoint (`/health`) monitors protocol connectivity:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.connected,
        # "coap_connected": coap_client.connected,
        # "ble_connected": ble_client.connected,
    }
```

### MQTT Communication (Current Implementation)

- MQTT service is initialized automatically on app startup (see `app/main.py:lifespan`)
- All MQTT operations via `app/services/mqtt_service.py`
- Topic format: `device/{device_id}/{message_type}`
- Message format: JSON
- MQTT client instance: `mqtt_client` (import from `app.services.mqtt_service`)

**Supported MQTT Message Types:**
- `data` - Sensor telemetry and measurements
- `status` - Device status updates (online/offline/error)
- `heartbeat` - Keep-alive signals
- `command/response` - Response to server commands
- `firmware/status` - Firmware upgrade progress

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
| `app/db/models/device.py` | Device model with protocol_type field for multi-protocol support |
| `alembic.ini` | Database migration configuration |
| `celery_worker.py` | Celery application configuration for firmware tasks |
| `docker-compose.yml` | Multi-service orchestration (MySQL, Redis, MQTT broker, app, worker) |
| `pytest.ini` | Test configuration and markers |
| `run_tests.py` | Custom test runner for simplified test execution |
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

## Adding Protocol Dependencies

When adding support for new IoT protocols, install required packages:

```bash
# CoAP support
pip install aiocoap

# Bluetooth/BLE support
pip install bleak

# Zigbee support
pip install zigpy-znp

# LoRaWAN support
pip install lorawan

# Z-Wave support
pip install openzwave

# Thread/Matter support
pip install matter-server

# AMQP support (RabbitMQ/ActiveMQ)
pip install pika  # For RabbitMQ
```

Add to `requirements.txt` with version constraints:
```
aiocoap==0.4.7
bleak==0.21.1
# ... other protocol libraries
```

## Protocol Infrastructure

### Current MQTT Broker (EMQX)
Docker Compose includes EMQX MQTT broker:
- **TCP**: `1883` (MQTT)
- **WebSocket**: `8083` (Web-based MQTT)
- **Dashboard**: `8080` (Management UI)

### Adding New Protocol Brokers

To add support for other protocols, add broker services to `docker-compose.yml`:

```yaml
# CoAP server (optional, or use built-in aiocoap)
  coap_server:
    image: californium/cf-coap:latest
    ports:
      - "5683:5683"

# RabbitMQ for AMQP
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

# Mosquitto (alternative MQTT broker)
  mosquitto:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
```

Update environment variables in `backend_app` service for protocol-specific configurations.

## Protocol Conversion & Data Aggregation

### Cross-Protocol Communication

Use the system to translate between protocols:

```python
# Example: Send MQTT command to CoAP device
mqtt_device = device_crud.get_by_id(db, mqtt_device_id)
coap_device = device_crud.get_by_id(db, coap_device_id)

# Translate MQTT message to CoAP format
if mqtt_device.metadata["protocol"] == "mqtt" and coap_device.metadata["protocol"] == "coap":
    coap_service.send_command(
        device_id=coap_device.device_id,
        command_data={
            "resource": "/actuator/control",
            "payload": mqtt_command.command_data,
            "method": "POST"
        }
    )
```

### Data Normalization

All protocol data is normalized to a common schema before storage:

```python
def normalize_device_data(device_id: str, protocol: str, raw_data: dict) -> DeviceDataCreate:
    """Normalize protocol-specific data to common format"""
    normalized = {
        "device_id": device_id,
        "protocol": protocol,  # Track original protocol
        "data_type": raw_data.get("type", "telemetry"),
        "data": raw_data.get("payload", raw_data),
        "quality": "good"
    }
    return DeviceDataCreate(**normalized)
```

### Gateway Pattern

For protocols requiring gateway bridges:

```python
# app/services/gateway_service.py
class GatewayService:
    def __init__(self):
        self.bridges = {
            "zigbee_to_mqtt": ZigbeeMQTTBridge(),
            "ble_to_mqtt": BleMQTTBridge(),
            # Add more bridges
        }

    async def route_message(self, source_protocol: str, target_protocol: str, message: dict):
        """Route message between protocols via gateway"""
        bridge_key = f"{source_protocol}_to_{target_protocol}"
        bridge = self.bridges.get(bridge_key)
        if bridge:
            return await bridge.translate(message)
        raise ValueError(f"No bridge available for {bridge_key}")
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
- **Code quality requirements**:
  - Functions < 50 lines
  - Classes < 200 lines
  - Files < 300 lines
  - Cyclomatic complexity < 10
- **Version control**:
  - Commit messages in Chinese: `类型: 简短描述`
  - Branch naming: `feature/功能名`, `bugfix/问题描述`, `hotfix/紧急修复`
- **Logging**: Use Python standard logging module with timestamps, level, module, and message

## Docker Services

The `docker-compose.yml` defines these services:
- **mysql_db**: MySQL 8.0 database
- **redis_cache**: Redis for caching and message broker
- **mqtt_broker**: EMQX MQTT broker
- **backend_app**: FastAPI application
- **celery_worker**: Celery worker for async tasks
- **frontend_app**: Vue.js frontend (if present)
- **nginx**: Reverse proxy and static file server
