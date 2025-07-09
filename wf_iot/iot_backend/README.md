
四、部署与运维考虑

#【1-Nginx配置】


#【2-docker-compose.yml】


#【3-数据库迁移】
# 1.数据库迁移: pip install alembic

# 2.初始化：alembic init migrations

# 3.配置 alembic.ini: 修改 sqlalchemy.url 指向你的MySQL数据库

# 4.在 env.py 中导⼊Base： from app.db.base import Base; target_metadata = Base.metadata

# 5.生成迁移脚本：alembic revision ----autogenerate -m "Initial migration"

# 6.执行迁移：alembic upgrade head



