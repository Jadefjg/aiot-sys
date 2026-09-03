# 作用：路由聚合，聚合所有API路由
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, devices, firmware, permissions, roles,
    products, alarms, groups, device_control, protocols, settings,
    links, smart, channels, rules, acl, overview, media,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(device_control.router, prefix="/devices", tags=["device-control"])
api_router.include_router(media.router, prefix="/devices", tags=["device-media"])
api_router.include_router(rules.shadow_router, prefix="/devices", tags=["device-shadow"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(groups.scenes_router, prefix="/scenes", tags=["scenes"])
api_router.include_router(groups.jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(smart.bindings_router, prefix="/bindings", tags=["bindings"])
api_router.include_router(smart.scripts_router, prefix="/scripts", tags=["scripts"])
api_router.include_router(links.router, prefix="/links", tags=["links"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(rules.rules_router, prefix="/rules", tags=["rules"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["firmware"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["protocols"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(acl.router, prefix="/acl", tags=["acl"])
api_router.include_router(overview.router, prefix="/overview", tags=["overview"])
