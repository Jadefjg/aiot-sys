# IoT设备管理系统部署文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (:80)                          │
│              前端静态文件 + API反向代理                   │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   Vue3 前端      │             │  FastAPI 后端   │
│   /dist静态文件  │             │     :8000       │
└─────────────────┘             └────────┬────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
            ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
            │   MySQL     │      │    Redis    │      │    EMQX     │
            │   :3306     │      │    :6379    │      │    :1883    │
            └─────────────┘      └─────────────┘      └─────────────┘
```

## 2. 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| 操作系统 | CentOS 8 / Alibaba Cloud Linux 3 | 64位 |
| Python | 3.8+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0+ / MariaDB 10.5+ | 数据库 |
| Redis | 6.0+ | 缓存/消息队列 |
| Docker | 20+ | 运行EMQX |
| Nginx | 1.20+ | 反向代理 |

## 3. 服务器环境准备

### 3.1 安装基础软件

```bash
# 安装 Python 3.8
yum install -y python38 python38-pip python38-devel

# 安装 Node.js 18 (如未安装)
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# 安装 rsync
yum install -y rsync

# 验证安装
python3.8 --version
node --version
```

### 3.2 配置 Docker 镜像加速 (国内服务器)

```bash
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
EOF
systemctl restart docker
```

## 4. 中间件配置

### 4.1 MySQL 数据库

```bash
# 创建数据库和用户
mysql -u root << 'EOF'
CREATE DATABASE IF NOT EXISTS iot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'iot_user'@'localhost' IDENTIFIED BY 'IoT2024SecurePwd';
CREATE USER IF NOT EXISTS 'iot_user'@'%' IDENTIFIED BY 'IoT2024SecurePwd';
GRANT ALL PRIVILEGES ON iot_db.* TO 'iot_user'@'localhost';
GRANT ALL PRIVILEGES ON iot_db.* TO 'iot_user'@'%';
FLUSH PRIVILEGES;
EOF
```

### 4.2 Redis

```bash
# 确认 Redis 运行
systemctl status redis
redis-cli ping  # 应返回 PONG
```

### 4.3 EMQX (Docker)

```bash
# 拉取并启动 EMQX
docker pull emqx/emqx:latest
docker run -d --name emqx \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8084:8084 \
  -p 8883:8883 \
  -p 18083:18083 \
  --restart always \
  emqx/emqx:latest

# 验证运行
docker ps | grep emqx
```

## 5. 后端部署

### 5.1 创建项目目录并上传代码

```bash
# 创建目录
mkdir -p /opt/iot_project

# 上传代码 (从本地执行)
rsync -avz --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.git' --exclude='venv' --exclude='.venv' \
  --exclude='node_modules' --exclude='dist' \
  iot_backend/ root@服务器IP:/opt/iot_project/iot_backend/
```

### 5.2 创建环境配置文件

```bash
cat > /opt/iot_project/iot_backend/.env << 'EOF'
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=iot_user
MYSQL_PASSWORD=IoT2024SecurePwd
MYSQL_DATABASE=iot_db

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0

# MQTT配置
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883

# JWT配置
SECRET_KEY=your-production-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Celery配置
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# 固件存储配置
FIRMWARE_UPLOAD_DIR=/opt/iot_project/firmware_storage
FIRMWARE_BASE_URL=http://你的服务器IP/firmware_files

# 应用配置
PROJECT_NAME=IoT Device Management System
DEBUG=False

# CORS配置
CORS_ORIGINS=http://你的服务器IP,http://localhost:5173
EOF
```

### 5.3 安装 Python 依赖

```bash
cd /opt/iot_project/iot_backend

# 创建虚拟环境
python3.8 -m venv venv
source venv/bin/activate

# 升级 pip 并安装依赖
pip install --upgrade pip
pip install -r requirements.txt
pip install email-validator
pip install 'bcrypt==4.0.1'  # 兼容性修复
```

### 5.4 配置 Alembic 数据库迁移

```bash
# 修改 alembic.ini 中的数据库连接
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = mysql+pymysql://iot_user:IoT2024SecurePwd@localhost:3306/iot_db|g' alembic.ini
```

更新 `migrations/env.py`:

```python
from logging.config import fileConfig
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.base import Base
from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.db.models.device import Device, DeviceData, DeviceCommand
from app.db.models.firmware import Firmware, FirmwareUpgradeTask

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 5.5 执行数据库迁移

```bash
cd /opt/iot_project/iot_backend
source venv/bin/activate

# 创建 versions 目录
mkdir -p migrations/versions

# 生成迁移脚本
alembic revision --autogenerate -m "initial migration"

# 执行迁移
alembic upgrade head
```

### 5.6 创建 Systemd 服务

```bash
cat > /etc/systemd/system/iot-backend.service << 'EOF'
[Unit]
Description=IoT Backend FastAPI Service
After=network.target mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iot_project/iot_backend
Environment="PATH=/opt/iot_project/iot_backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/opt/iot_project/iot_backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable iot-backend
systemctl start iot-backend
systemctl status iot-backend
```

### 5.7 创建管理员用户

```bash
cd /opt/iot_project/iot_backend
source venv/bin/activate

python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from app.db.base import Base
from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.db.models.device import Device, DeviceData, DeviceCommand
from app.db.models.firmware import Firmware, FirmwareUpgradeTask
from app.db.session import SessionLocal
from app.core.security import get_password_hash

db = SessionLocal()

# 创建管理员角色
admin_role = db.query(Role).filter(Role.name == 'admin').first()
if not admin_role:
    admin_role = Role(name='admin', description='系统管理员')
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

# 创建管理员用户
admin_user = db.query(User).filter(User.username == 'admin').first()
if not admin_user:
    admin_user = User(
        username='admin',
        email='admin@iot.local',
        hashed_password=get_password_hash('admin123'),
        full_name='系统管理员',
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    db.add(user_role)
    db.commit()
    print('管理员创建成功: admin / admin123')

db.close()
EOF
```

## 6. 前端部署

### 6.1 上传前端代码

```bash
# 从本地执行
rsync -avz --exclude='node_modules' --exclude='dist' --exclude='.git' \
  iot_web/ root@服务器IP:/opt/iot_project/iot_web/
```

### 6.2 构建前端

```bash
cd /opt/iot_project/iot_web
npm install
npm run build
```

## 7. Nginx 配置

```bash
cat > /etc/nginx/conf.d/iot.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件
    root /opt/iot_project/iot_web/dist;
    index index.html;

    # 前端路由 - SPA支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Swagger文档
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }

    # 固件文件
    location /firmware_files/ {
        alias /opt/iot_project/firmware_storage/;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
EOF

# 测试并重载配置
nginx -t
systemctl reload nginx
```

## 8. 系统验证

```bash
# 检查服务状态
systemctl status iot-backend
systemctl status nginx
docker ps | grep emqx

# 测试前端访问
curl -I http://localhost/

# 测试API
curl http://localhost/api/v1/

# 测试登录
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## 9. 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://服务器IP/ | 管理系统入口 |
| API文档 | http://服务器IP/docs | Swagger文档 |
| EMQX控制台 | http://服务器IP:18083 | 默认 admin/public |

**默认登录凭据**: `admin` / `admin123`

## 10. 常用运维命令

```bash
# 后端服务管理
systemctl start iot-backend
systemctl stop iot-backend
systemctl restart iot-backend
systemctl status iot-backend

# 查看后端日志
journalctl -u iot-backend -f
journalctl -u iot-backend -n 100

# Nginx管理
systemctl reload nginx
nginx -t

# EMQX管理
docker restart emqx
docker logs emqx -f

# 数据库连接
mysql -u iot_user -p'IoT2024SecurePwd' iot_db
```

## 11. 故障排查

### 后端无法启动

```bash
# 查看详细日志
journalctl -u iot-backend -n 100 --no-pager

# 手动测试启动
cd /opt/iot_project/iot_backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 数据库连接失败

```bash
# 测试数据库连接
mysql -u iot_user -p'IoT2024SecurePwd' -h localhost iot_db -e "SELECT 1"

# 检查密码中的特殊字符
# 密码不要包含 @ 等特殊字符，否则需要URL编码
```

### 端口被占用

```bash
# 查看端口占用
lsof -ti:8000
netstat -tlnp | grep 8000

# 强制释放端口
lsof -ti:8000 | xargs kill -9
```

### EMQX 无法启动

```bash
# 查看容器日志
docker logs emqx

# 重新创建容器
docker rm -f emqx
docker run -d --name emqx -p 1883:1883 -p 18083:18083 --restart always emqx/emqx:latest
```

## 12. 安全建议

1. **修改默认密码**: 部署后立即修改 admin 用户密码
2. **配置防火墙**: 只开放必要端口 (80, 443, 1883)
3. **配置HTTPS**: 生产环境建议配置 SSL 证书
4. **定期备份**: 配置 MySQL 定期备份策略
5. **更新SECRET_KEY**: 修改 `.env` 中的 JWT 密钥
