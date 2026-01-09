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