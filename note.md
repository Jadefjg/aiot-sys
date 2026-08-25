阿里云服务器：39.108.180.245 root / 


IoT系统部署完成！

  访问地址

  - 前端界面: http://39.108.180.245
  - API文档: http://39.108.180.245/docs
  - EMQX控制台: http://39.108.180.245:18083 (默认 admin/public)

  登录凭据

  - 用户名: admin
  - 密码: admin123

  部署架构

  | 服务                  | 端口            | 状态       |
  |-----------------------|-----------------|------------|
  | Nginx (前端+反向代理) | 80              | ✅ Running |
  | FastAPI 后端          | 8000            | ✅ Running |
  | MySQL (MariaDB)       | 3306            | ✅ Running |
  | Redis                 | 6379            | ✅ Running |
  | EMQX (MQTT)           | 1883/8083/18083 | ✅ Running |

  关键配置文件

  - 后端配置: /opt/iot_project/iot_backend/.env
  - Nginx配置: /etc/nginx/conf.d/iot.conf
  - Systemd服务: /etc/systemd/system/iot-backend.service

  常用运维命令

  # 服务管理
  systemctl status iot-backend    # 后端状态
  systemctl restart iot-backend   # 重启后端
  systemctl status nginx          # Nginx状态
  docker ps                       # EMQX容器状态

  # 日志查看
  journalctl -u iot-backend -f    # 后端日志
  tail -f /var/log/nginx/access.log  # Nginx日志

  # 数据库
  mysql -u iot_user -p'IoT2024SecurePwd' iot_db


  统访问信息

  访问地址

  | 服务       | 地址                        | 说明            |
  |------------|-----------------------------|-----------------|
  | 前端界面   | http://39.108.180.245       | IoT管理系统入口 |
  | API文档    | http://39.108.180.245/docs  | Swagger接口文档 |
  | EMQX控制台 | http://39.108.180.245:18083 | MQTT管理后台    |

  登录账户

  IoT管理系统:
  - 用户名: admin
  - 密码: admin123

  EMQX控制台:
  - 用户名: admin
  - 密码: public






后端：
cd iot_backend
source .venv/bin/activate
pip install -r requirements.txt   # 可选，已装好
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


前端：
cd iot_web
npm run dev


登录凭据
- 用户名: admin
- 密码: admin123



# 1) 基础设施（Docker Desktop 需已打开）
cd iot_backend
docker compose up -d mysql_db redis_cache mqtt_broker

# 2) 后端
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3) 初始化账号（另开终端）
cd iot_backend && source .venv/bin/activate
python scripts/seed_users.py



方案：一键部署
cd /Users/mark/Documents/0Study/aiot-sys
docker compose up -d --build
docker compose ps


服务	URL
控制台   http://localhost/iot/
API     http://localhost/api/v1/
Swagger http://localhost/docs
EMQX    http://localhost:18083
MQTT    localhost:1883
健康检查  http://localhost:8080/health

账号密码：admin / admin123

docker compose logs -f backend_app    # 看后端日志
docker compose restart backend_app    # 重启后端
docker compose down                   # 停止（保留数据）
docker compose down -v                # 停止并清空数据卷