# 用户模块接口测试文档

## 概述

本文档描述了IoT后端系统用户模块的接口测试脚本，包括测试用例、测试数据和运行方法。

## 测试结构

```
test/
├── api/                    # API接口测试
│   ├── test_api_users.py   # 用户模块API测试
│   └── test_api_auth.py    # 认证模块API测试
├── conftest.py            # 测试配置和fixtures
├── pytest.ini            # pytest配置文件
└── README.md              # 测试文档
```

## 测试文件说明

### 1. test_api_users.py

用户模块API测试，包含以下测试用例：

#### 用户创建测试
- `test_create_user_success`: 测试成功创建用户
- `test_create_user_duplicate_username`: 测试创建重复用户名的用户
- `test_create_user_duplicate_email`: 测试创建重复邮箱的用户
- `test_create_user_unauthorized`: 测试无权限创建用户
- `test_create_user_insufficient_permissions`: 测试权限不足创建用户

#### 用户列表测试
- `test_get_users_list_success`: 测试成功获取用户列表
- `test_get_users_list_unauthorized`: 测试无权限获取用户列表
- `test_get_users_list_insufficient_permissions`: 测试权限不足获取用户列表

#### 当前用户测试
- `test_get_current_user_success`: 测试成功获取当前用户信息
- `test_get_current_user_unauthorized`: 测试无权限获取当前用户信息
- `test_update_current_user_success`: 测试成功更新当前用户信息
- `test_update_current_user_password`: 测试更新当前用户密码
- `test_update_current_user_unauthorized`: 测试无权限更新当前用户信息

#### 用户管理测试
- `test_get_user_by_id_success`: 测试成功根据ID获取用户信息
- `test_get_user_by_id_self_access`: 测试用户获取自己的信息
- `test_get_user_by_id_unauthorized`: 测试无权限根据ID获取用户信息
- `test_get_user_by_id_not_found`: 测试获取不存在的用户信息
- `test_get_user_by_id_insufficient_permissions`: 测试权限不足获取其他用户信息
- `test_update_user_success`: 测试成功更新指定用户信息
- `test_update_user_not_found`: 测试更新不存在的用户
- `test_update_user_unauthorized`: 测试无权限更新用户信息

#### 令牌测试
- `test_invalid_token`: 测试无效令牌
- `test_expired_token`: 测试过期令牌

#### 数据验证测试
- `test_user_validation_errors`: 测试用户数据验证错误
- `test_missing_required_fields`: 测试缺少必填字段

### 2. test_api_auth.py

认证模块API测试，包含以下测试用例：

#### 登录测试
- `test_login_success`: 测试成功登录
- `test_login_invalid_username`: 测试无效用户名登录
- `test_login_invalid_password`: 测试无效密码登录
- `test_login_inactive_user`: 测试非活跃用户登录
- `test_login_missing_username`: 测试缺少用户名登录
- `test_login_missing_password`: 测试缺少密码登录
- `test_login_empty_credentials`: 测试空凭据登录

#### 令牌验证测试
- `test_test_token_success`: 测试令牌验证成功
- `test_test_token_invalid_token`: 测试无效令牌
- `test_test_token_missing_token`: 测试缺少令牌
- `test_test_token_expired_token`: 测试过期令牌
- `test_test_token_malformed_token`: 测试格式错误的令牌

#### 安全测试
- `test_login_case_sensitivity`: 测试用户名大小写敏感性
- `test_password_case_sensitivity`: 测试密码大小写敏感性
- `test_login_rate_limiting`: 测试登录频率限制
- `test_concurrent_login_attempts`: 测试并发登录尝试

### 3. conftest.py

测试配置和fixtures，提供：

#### 数据库fixtures
- `db_engine`: 测试数据库引擎
- `db`: 数据库会话

#### 测试客户端fixtures
- `client`: 测试客户端

#### 测试数据fixtures
- `test_user_data`: 测试用户数据
- `test_superuser_data`: 测试超级用户数据
- `sample_users_data`: 批量测试用户数据

#### 用户fixtures
- `created_user`: 创建的测试用户
- `created_superuser`: 创建的测试超级用户
- `created_users`: 批量创建的测试用户

#### 认证fixtures
- `user_token`: 普通用户访问令牌
- `superuser_token`: 超级用户访问令牌

## 运行测试

### 1. 安装依赖

```bash
pip install pytest pytest-cov fastapi[all] sqlalchemy
```

### 2. 运行所有测试

```bash
# 使用pytest直接运行
pytest test/api/ -v

# 或使用提供的脚本
python run_tests.py
```

### 3. 运行特定测试文件

```bash
# 运行用户模块测试
pytest test/api/test_api_users.py -v

# 运行认证模块测试
pytest test/api/test_api_auth.py -v
```

### 4. 运行特定测试用例

```bash
# 运行特定测试方法
pytest test/api/test_api_users.py::TestUserAPI::test_create_user_success -v

# 运行特定测试类
pytest test/api/test_api_users.py::TestUserAPI -v
```

### 5. 生成覆盖率报告

```bash
# 使用pytest-cov
pytest --cov=app --cov-report=html --cov-report=term-missing test/api/

# 或使用脚本
python run_tests.py --coverage
```

## 测试配置

### pytest.ini

```ini
[tool:pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### 环境变量

测试使用以下环境变量：

- `TESTING=1`: 标识测试环境
- `DATABASE_URL=sqlite:///./test.db`: 测试数据库URL

## 测试数据

### 测试用户数据

```python
test_user_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123",
    "full_name": "Test User",
    "is_superuser": False
}
```

### 测试超级用户数据

```python
test_superuser_data = {
    "username": "superuser",
    "email": "superuser@example.com",
    "password": "superpassword123",
    "full_name": "Super User",
    "is_superuser": True
}
```

## 测试覆盖范围

测试覆盖以下API端点：

### 用户模块
- `GET /api/v1/users/` - 获取用户列表
- `POST /api/v1/users/` - 创建用户
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `GET /api/v1/users/{user_id}` - 根据ID获取用户信息
- `PUT /api/v1/users/{user_id}` - 更新指定用户信息

### 认证模块
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/test-token` - 验证令牌

## 注意事项

1. **数据库隔离**: 每个测试使用独立的数据库会话，确保测试之间不相互影响

2. **数据清理**: 测试结束后自动清理测试数据

3. **权限测试**: 测试涵盖了不同的权限级别和访问控制

4. **错误处理**: 测试了各种错误情况和异常处理

5. **安全测试**: 包含了令牌验证、权限检查等安全相关测试

## 扩展测试

要添加新的测试用例：

1. 在相应的测试文件中添加新的测试方法
2. 使用`test_`前缀命名测试方法
3. 添加必要的fixtures和测试数据
4. 确保测试的独立性和可重复性

## 故障排除

### 常见问题

1. **数据库连接错误**: 检查数据库配置和连接字符串
2. **导入错误**: 确保所有依赖已正确安装
3. **权限错误**: 检查测试用户的权限设置
4. **令牌错误**: 验证JWT配置和密钥设置

### 调试技巧

1. 使用`-s`参数查看print输出
2. 使用`--pdb`进入调试模式
3. 使用`--tb=long`查看详细错误信息
4. 单独运行失败的测试用例进行调试
