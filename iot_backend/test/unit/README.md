# Unit Tests

本目录包含项目各个模块的单元测试。

## 测试文件说明

- `test_crud_user.py` - 用户CRUD模块测试（CRUDUser, CRUDRole, CRUDPermission）
- `test_crud_device.py` - 设备CRUD模块测试（CRUDDevice, CRUDDeviceData, CRUDDeviceCommand）
- `test_crud_permission.py` - 权限CRUD模块测试（CRUDPermission）
- `test_core_security.py` - 安全模块测试（密码哈希、JWT令牌）
- `test_schemas.py` - Pydantic Schema 测试（数据验证和序列化）

## 运行测试

### 运行所有单元测试
```bash
pytest test/unit/ -v
```

### 运行特定测试文件
```bash
pytest test/unit/test_crud_user.py -v
pytest test/unit/test_core_security.py -v
```

### 运行特定测试类
```bash
pytest test/unit/test_crud_user.py::TestCRUDUser -v
```

### 运行特定测试方法
```bash
pytest test/unit/test_crud_user.py::TestCRUDUser::test_get_user_by_id_success -v
```

### 查看测试覆盖率
```bash
pytest test/unit/ --cov=app --cov-report=html
```

### 只运行标记为 unit 的测试
```bash
pytest -m unit -v
```

## 测试结构

每个测试文件都遵循以下结构：

1. **Fixtures** - 提供测试所需的模拟对象和数据
2. **测试类** - 按功能组织测试用例
3. **测试方法** - 每个方法测试一个特定功能
4. **边界情况测试** - 测试边界条件和异常情况

## 测试原则

- **隔离性**: 使用 mock 隔离外部依赖（数据库、网络等）
- **可重复性**: 测试结果应该可重复且一致
- **清晰性**: 测试名称清晰描述测试内容
- **全面性**: 覆盖正常流程和异常情况

## Mock 使用

单元测试使用 `unittest.mock` 进行依赖隔离：

- `MagicMock` - 模拟对象和方法
- `patch` - 临时替换模块或函数
- `@patch` - 装饰器形式的 patch

## Fixtures

共享的 fixtures 定义在 `conftest.py` 中：

- `test_settings` - 测试环境配置
- `sample_user_data` - 示例用户数据
- `sample_device_data` - 示例设备数据
- `sample_permission_data` - 示例权限数据

## 测试覆盖

当前单元测试覆盖以下模块：

### CRUD 层
- ✅ User CRUD (创建、读取、更新、删除、认证)
- ✅ Device CRUD (设备管理、状态更新)
- ✅ Device Data CRUD (数据记录)
- ✅ Device Command CRUD (命令管理)
- ✅ Permission CRUD (权限管理)

### Core 层
- ✅ Security (密码哈希、JWT令牌)

### Schema 层
- ✅ User Schemas
- ✅ Device Schemas
- ✅ Permission Schemas
- ✅ Firmware Schemas
- ✅ Token Schemas

## 持续改进

后续可以添加的测试：

- [ ] Services 层测试（MQTT, Firmware 等）
- [ ] Utils 工具函数测试
- [ ] Dependencies 依赖注入测试
- [ ] 更多边界情况和异常处理测试
