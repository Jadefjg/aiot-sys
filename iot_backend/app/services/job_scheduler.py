"""定时任务调度：按 HH:MM + 星期执行动作"""
import json
import logging
import threading
import uuid
from datetime import datetime

from app.db.session import SessionLocal
from app.crud.group import job_crud
from app.crud.device import device_crud

logger = logging.getLogger(__name__)


class JobScheduler:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = None
        self._fired = set()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Job scheduler started")

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(20):
            self._tick()

    def _tick(self):
        now = datetime.now()
        key_day = now.strftime("%Y-%m-%d")
        hhmm = now.strftime("%H:%M")
        db = SessionLocal()
        try:
            for job in job_crud.get_multi(db, limit=500):
                if not job.enabled or not job.cron_time:
                    continue
                if job.weekdays is not None and now.weekday() not in job.weekdays:
                    continue
                cron = (job.cron_time or "")[:5]
                stamp = f"{job.id}:{key_day}:{cron}"
                if cron != hhmm or stamp in self._fired:
                    continue
                self._fired.add(stamp)
                self._run_job(db, job)
                if job.once:
                    job.enabled = False
                    db.add(job)
                    db.commit()
            self._fired = {k for k in self._fired if f":{key_day}:" in k}
            self._mark_stale_offline(db)
            try:
                from app.services.script_engine import script_engine
                script_engine.tick(db)
            except Exception as exc:
                logger.warning("Script tick: %s", exc)
            prune_key = f"prune:{key_day}:03:15"
            if hhmm == "03:15" and prune_key not in self._fired:
                self._fired.add(prune_key)
                from app.crud.device import prune_old_device_data
                deleted = prune_old_device_data(db)
                if deleted:
                    logger.info("Pruned %s old device_data rows", deleted)
        except Exception as exc:
            logger.error("Job tick error: %s", exc)
        finally:
            db.close()

    def _run_job(self, db, job):
        from app.services.mqtt_service import mqtt_client
        from app.services.device_runtime_service import device_runtime

        action = job.action or {}
        device_id = action.get("device_id")
        if not device_id:
            logger.info("Job %s fired without device", job.name)
            return
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            return
        kind = action.get("type") or "write"
        msg_id = str(uuid.uuid4())
        if kind == "action":
            payload = {
                "msg_id": msg_id,
                "device_id": device_id,
                "action": action.get("action") or "default",
                "params": job.data or {},
            }
            topic = device_runtime._target_topic(device, "action")
        else:
            payload = {
                "msg_id": msg_id,
                "device_id": device_id,
                "values": job.data or action.get("values") or {},
            }
            topic = device_runtime._target_topic(device, "write")
        mqtt_client.publish(topic, json.dumps(payload))
        logger.info("Job executed: %s -> %s", job.name, device_id)

    def _mark_stale_offline(self, db) -> None:
        """超过 5 分钟无心跳的在线设备标记离线"""
        from datetime import timedelta

        from sqlalchemy import or_

        from app.db.models.device import Device

        cutoff = datetime.utcnow() - timedelta(minutes=5)
        stale = (
            db.query(Device)
            .filter(Device.status == "online")
            .filter(or_(Device.last_online_at.is_(None), Device.last_online_at < cutoff))
            .limit(200)
            .all()
        )
        for device in stale:
            device.status = "offline"
            db.add(device)
        if stale:
            db.commit()
            logger.info("Marked %s devices offline by heartbeat", len(stale))


job_scheduler = JobScheduler()
