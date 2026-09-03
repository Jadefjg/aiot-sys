from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.protocol_manager import protocol_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("Starting IOT Backend Service...")

    # 确保物联中台相关表结构
    try:
        from app.db.init_db import ensure_schema
        ensure_schema()
        print("✓ Database schema ready")
    except Exception as e:
        print(f"✗ Database schema init: {e}")

    # 初始化协议管理器
    protocol_manager.initialize()

    # 启动所有协议服务 (MQTT, CoAP, AMQP等)
    startup_results = await protocol_manager.start_all()

    # 记录启动状态
    for protocol, success in startup_results.items():
        status = "✓" if success else "✗"
        print(f"{status} {protocol.upper()} service: {'Started' if success else 'Failed'}")

    try:
        from app.services.job_scheduler import job_scheduler
        job_scheduler.start()
        print("✓ Job scheduler: Started")
    except Exception as e:
        print(f"✗ Job scheduler: {e}")

    yield

    # 关闭时执行
    print("Shutting down IOT Backend Service...")

    try:
        from app.services.job_scheduler import job_scheduler
        job_scheduler.stop()
    except Exception:
        pass

    # 停止所有协议服务
    shutdown_results = await protocol_manager.stop_all()

    # 记录关闭状态
    for protocol, success in shutdown_results.items():
        status = "✓" if success else "✗"
        print(f"{status} {protocol.upper()} service: {'Stopped' if success else 'Failed'}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # "/api/v1/openapi.json"
    lifespan=lifespan,
)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# 包含API路由
app.include_router(api_router,prefix=settings.API_V1_STR) # prefix="/api/v1"

try:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles

    media_dir = Path(settings.MEDIA_UPLOAD_DIR)
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media_files", StaticFiles(directory=str(media_dir)), name="media_files")
except Exception:
    pass

@app.get("/")
async def root():
    return {
        "message": "IOT Backend Service",
        "version": settings.PROJECT_VERSION,
        "status": "Running",
    }

@app.get("/health")
async def health_check():
    """健康检查：进程存活即 healthy，协议详情仅作附加信息"""
    from datetime import datetime, timezone

    try:
        protocol_statuses = protocol_manager.get_service_status() or []
    except Exception as e:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocols": {},
            "warning": str(e),
        }

    protocols = {}
    for status in protocol_statuses:
        if not status:
            continue
        protocols[status["protocol"]] = {
            "connected": status.get("connected", False),
            "device_count": status.get("device_count", 0),
        }

    from app.services.timeseries import timeseries

    influx = {"enabled": timeseries.enabled, "connected": False}
    if timeseries.enabled:
        influx["connected"] = timeseries.ping()

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "protocols": protocols,
        "all_protocols_connected": all(
            p.get("connected") for p in protocols.values()
        ) if protocols else False,
        "influx": influx,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
