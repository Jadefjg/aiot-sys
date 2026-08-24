-- =====================================================
-- 微服务数据库初始化脚本
-- 创建3个独立数据库：iot_auth_db, iot_device_db, iot_firmware_db
-- =====================================================

-- 创建认证服务数据库
CREATE DATABASE IF NOT EXISTS iot_auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建设备服务数据库
CREATE DATABASE IF NOT EXISTS iot_device_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建固件服务数据库
CREATE DATABASE IF NOT EXISTS iot_firmware_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建服务专用用户（可选，生产环境建议为每个服务创建独立用户）
-- CREATE USER IF NOT EXISTS 'auth_service'@'%' IDENTIFIED BY 'auth_password';
-- CREATE USER IF NOT EXISTS 'device_service'@'%' IDENTIFIED BY 'device_password';
-- CREATE USER IF NOT EXISTS 'firmware_service'@'%' IDENTIFIED BY 'firmware_password';

-- 授权
-- GRANT ALL PRIVILEGES ON iot_auth_db.* TO 'auth_service'@'%';
-- GRANT ALL PRIVILEGES ON iot_device_db.* TO 'device_service'@'%';
-- GRANT ALL PRIVILEGES ON iot_firmware_db.* TO 'firmware_service'@'%';

-- 为方便开发，给root用户授予所有数据库权限
GRANT ALL PRIVILEGES ON iot_auth_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON iot_device_db.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON iot_firmware_db.* TO 'root'@'%';

FLUSH PRIVILEGES;

-- =====================================================
-- iot_auth_db 表结构
-- =====================================================
USE iot_auth_db;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_supperuser BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    INDEX idx_name (name),
    INDEX idx_resource_action (resource, action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户（密码: admin123，使用bcrypt哈希）
INSERT INTO users (username, email, hashed_password, full_name, is_active, is_supperuser)
VALUES ('admin', 'admin@iot.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4RDYJZJ.ZdvCp', 'System Admin', TRUE, TRUE)
ON DUPLICATE KEY UPDATE username = username;

-- 插入默认角色
INSERT INTO roles (name, description) VALUES
    ('admin', '系统管理员，拥有所有权限'),
    ('operator', '操作员，可管理设备'),
    ('viewer', '查看者，只读权限')
ON DUPLICATE KEY UPDATE name = name;

-- 插入默认权限
INSERT INTO permissions (name, description, resource, action) VALUES
    ('device:read', '查看设备', 'device', 'read'),
    ('device:write', '创建/更新设备', 'device', 'write'),
    ('device:delete', '删除设备', 'device', 'delete'),
    ('firmware:read', '查看固件', 'firmware', 'read'),
    ('firmware:write', '上传固件', 'firmware', 'write'),
    ('firmware:delete', '删除固件', 'firmware', 'delete'),
    ('user:read', '查看用户', 'user', 'read'),
    ('user:write', '管理用户', 'user', 'write'),
    ('user:delete', '删除用户', 'user', 'delete'),
    ('role:read', '查看角色', 'role', 'read'),
    ('role:write', '管理角色', 'role', 'write')
ON DUPLICATE KEY UPDATE name = name;

-- =====================================================
-- iot_device_db 表结构
-- =====================================================
USE iot_device_db;

CREATE TABLE IF NOT EXISTS devices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    device_id VARCHAR(100) NOT NULL UNIQUE,
    device_name VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    device_type VARCHAR(100),
    owner_id INT,                    -- 关联auth_db.users.id（跨库引用，无外键）
    status VARCHAR(20) DEFAULT 'offline',
    last_online_at DATETIME,
    firmware_version VARCHAR(50),
    hardware_version VARCHAR(50),
    latitude DOUBLE,
    longitude DOUBLE,
    device_metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_product_id (product_id),
    INDEX idx_owner_id (owner_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS device_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_type VARCHAR(50),
    data JSON NOT NULL,
    quality VARCHAR(50) DEFAULT 'good',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_data_type (data_type),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS device_commands (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,
    command_type VARCHAR(50) NOT NULL,
    command_data JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at DATETIME,
    acknowledged_at DATETIME,
    response_data JSON,
    created_by INT,                   -- 关联auth_db.users.id
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_status (status),
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- iot_firmware_db 表结构
-- =====================================================
USE iot_firmware_db;

CREATE TABLE IF NOT EXISTS firmware (
    id INT PRIMARY KEY AUTO_INCREMENT,
    version VARCHAR(50) NOT NULL UNIQUE,
    product_id VARCHAR(100) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64),
    description TEXT,
    release_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_beta BOOLEAN DEFAULT FALSE,
    min_hardware_version VARCHAR(50),
    created_by INT,                   -- 关联auth_db.users.id
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_version (version),
    INDEX idx_product_id (product_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS firmware_upgrade_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id INT NOT NULL,           -- 关联device_db.devices.id（跨库引用）
    device_identifier VARCHAR(100) NOT NULL,  -- 冗余存储device_id字符串
    firmware_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress INT DEFAULT 0,
    celery_task_id VARCHAR(100),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_device_id (device_id),
    INDEX idx_device_identifier (device_identifier),
    INDEX idx_firmware_id (firmware_id),
    INDEX idx_status (status),
    INDEX idx_celery_task_id (celery_task_id),
    FOREIGN KEY (firmware_id) REFERENCES firmware(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
