#!/bin/sh
set -e

echo "[entrypoint] waiting for MySQL ${MYSQL_HOST}:${MYSQL_PORT} ..."
i=0
until python - <<'PY'
import os, sys
import pymysql
try:
    pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "iot_user"),
        password=os.environ.get("MYSQL_PASSWORD", "password"),
        database=os.environ.get("MYSQL_DATABASE", "iot_db"),
        connect_timeout=3,
    ).close()
except Exception as e:
    print(e)
    sys.exit(1)
PY
do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "[entrypoint] MySQL not ready after 120s"
    exit 1
  fi
  sleep 2
done
echo "[entrypoint] MySQL is ready"

echo "[entrypoint] seeding default users ..."
cd /app
PYTHONPATH=/app python scripts/seed_users.py || echo "[entrypoint] seed users skipped/failed"

echo "[entrypoint] seeding default products ..."
PYTHONPATH=/app python scripts/seed_products.py || echo "[entrypoint] seed products skipped/failed"

exec "$@"
