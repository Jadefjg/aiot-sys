<template>
  <div class="permissions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>权限管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加权限
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索权限名称或代码"
          style="width: 300px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="resourceFilter" placeholder="资源类型" clearable style="width: 150px; margin-left: 10px">
          <el-option label="用户" value="user" />
          <el-option label="设备" value="device" />
          <el-option label="固件" value="firmware" />
          <el-option label="角色" value="role" />
          <el-option label="权限" value="permission" />
        </el-select>
      </div>

      <!-- 权限列表 -->
      <el-table :data="filteredPermissions" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="权限名称" width="150" />
        <el-table-column prop="code" label="权限代码" width="200">
          <template #default="{ row }">
            <el-tag type="info">{{ row.code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource" label="资源类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getResourceType(row.resource)">
              {{ getResourceText(row.resource) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作类型" width="100">
          <template #default="{ row }">
            {{ getActionText(row.action) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑权限对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="isEditing ? '编辑权限' : '添加权限'"
      width="500px"
    >
      <el-form ref="permissionFormRef" :model="permissionForm" :rules="permissionRules" label-width="100px">
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="请输入权限名称" />
        </el-form-item>
        <el-form-item label="权限代码" prop="code">
          <el-input
            v-model="permissionForm.code"
            :disabled="isEditing"
            placeholder="请输入权限代码，如 device:read"
          />
        </el-form-item>
        <el-form-item label="资源类型" prop="resource">
          <el-select v-model="permissionForm.resource" placeholder="请选择资源类型" style="width: 100%">
            <el-option label="用户" value="user" />
            <el-option label="设备" value="device" />
            <el-option label="固件" value="firmware" />
            <el-option label="角色" value="role" />
            <el-option label="权限" value="permission" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型" prop="action">
          <el-select v-model="permissionForm.action" placeholder="请选择操作类型" style="width: 100%">
            <el-option label="查看" value="read" />
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="permissionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePermissionSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPermissions, getPermission, createPermission, updatePermission, deletePermission } from '@/api/modules/permissions'

// 状态
const loading = ref(false)
const submitLoading = ref(false)
const permissions = ref([])
const searchKeyword = ref('')
const resourceFilter = ref('')

// 对话框状态
const permissionDialogVisible = ref(false)
const isEditing = ref(false)
const selectedPermission = ref(null)

// 表单
const permissionFormRef = ref(null)
const permissionForm = reactive({
  name: '',
  code: '',
  resource: '',
  action: '',
  description: ''
})

const permissionRules = {
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限代码', trigger: 'blur' },
    { pattern: /^[a-z_]+:[a-z_]+$/, message: '权限代码格式：resource:action', trigger: 'blur' }
  ],
  resource: [
    { required: true, message: '请选择资源类型', trigger: 'change' }
  ],
  action: [
    { required: true, message: '请选择操作类型', trigger: 'change' }
  ]
}

// 计算属性：过滤后的权限列表
const filteredPermissions = computed(() => {
  let result = permissions.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(keyword) ||
      p.code.toLowerCase().includes(keyword)
    )
  }
  if (resourceFilter.value) {
    result = result.filter(p => p.resource === resourceFilter.value)
  }
  return result
})

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取资源类型标签颜色
const getResourceType = (resource) => {
  const types = {
    user: 'primary',
    device: 'success',
    firmware: 'warning',
    role: 'danger',
    permission: 'info'
  }
  return types[resource] || 'info'
}

// 获取资源类型文本
const getResourceText = (resource) => {
  const texts = {
    user: '用户',
    device: '设备',
    firmware: '固件',
    role: '角色',
    permission: '权限'
  }
  return texts[resource] || resource
}

// 获取操作类型文本
const getActionText = (action) => {
  const texts = {
    read: '查看',
    create: '创建',
    update: '更新',
    delete: '删除',
    all: '全部'
  }
  return texts[action] || action
}

// 获取权限列表
const fetchPermissions = async () => {
  loading.value = true
  try {
    permissions.value = await getPermissions()
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEditing.value = false
  Object.assign(permissionForm, {
    name: '',
    code: '',
    resource: '',
    action: '',
    description: ''
  })
  permissionDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (permission) => {
  isEditing.value = true
  selectedPermission.value = permission
  Object.assign(permissionForm, {
    name: permission.name,
    code: permission.code,
    resource: permission.resource || '',
    action: permission.action || '',
    description: permission.description || ''
  })
  permissionDialogVisible.value = true
}

// 提交权限表单
const handlePermissionSubmit = async () => {
  if (!permissionFormRef.value) return

  await permissionFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEditing.value) {
          await updatePermission(selectedPermission.value.id, {
            name: permissionForm.name,
            resource: permissionForm.resource,
            action: permissionForm.action,
            description: permissionForm.description
          })
          ElMessage.success('权限更新成功')
        } else {
          await createPermission(permissionForm)
          ElMessage.success('权限添加成功')
        }
        permissionDialogVisible.value = false
        await fetchPermissions()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error(isEditing.value ? '更新失败' : '添加失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 删除权限
const handleDelete = async (permission) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${permission.name}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await deletePermission(permission.id)
    ElMessage.success('权限删除成功')
    await fetchPermissions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchPermissions()
})
</script>

<style scoped>
.permissions-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
</style>
