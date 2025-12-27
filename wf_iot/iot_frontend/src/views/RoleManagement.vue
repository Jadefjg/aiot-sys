<template>
  <div class="roles-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加角色
          </el-button>
        </div>
      </template>

      <!-- 角色列表 -->
      <el-table :data="roles" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="permissions" label="权限数量" width="120">
          <template #default="{ row }">
            <el-tag type="info">{{ row.permissions?.length || 0 }} 个权限</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" @click="showPermissionDialog(row)">
              分配权限
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="isEditing ? '编辑角色' : '添加角色'"
      width="500px"
    >
      <el-form ref="roleFormRef" :model="roleForm" :rules="roleRules" label-width="100px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRoleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 分配权限对话框 -->
    <el-dialog v-model="permissionDialogVisible" title="分配权限" width="600px">
      <div class="permission-info">
        <p><strong>角色:</strong> {{ selectedRole?.name }}</p>
      </div>
      <el-divider content-position="left">选择权限</el-divider>
      <div class="permission-list">
        <el-checkbox-group v-model="selectedPermissionIds">
          <el-row>
            <el-col :span="12" v-for="permission in availablePermissions" :key="permission.id">
              <el-checkbox :label="permission.id" class="permission-checkbox">
                <div class="permission-item">
                  <span class="permission-name">{{ permission.name }}</span>
                  <span class="permission-code">{{ permission.code }}</span>
                </div>
              </el-checkbox>
            </el-col>
          </el-row>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssignPermissions" :loading="permissionLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoles, getRole, createRole, updateRole, deleteRole, assignPermissions } from '@/api/modules/roles'
import { getPermissions } from '@/api/modules/permissions'

// 状态
const loading = ref(false)
const submitLoading = ref(false)
const permissionLoading = ref(false)
const roles = ref([])

// 对话框状态
const roleDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const isEditing = ref(false)
const selectedRole = ref(null)
const selectedPermissionIds = ref([])
const availablePermissions = ref([])

// 表单
const roleFormRef = ref(null)
const roleForm = reactive({
  name: '',
  description: ''
})

const roleRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在2-50个字符', trigger: 'blur' }
  ]
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取角色列表
const fetchRoles = async () => {
  loading.value = true
  try {
    roles.value = await getRoles()
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEditing.value = false
  Object.assign(roleForm, {
    name: '',
    description: ''
  })
  roleDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (role) => {
  isEditing.value = true
  selectedRole.value = role
  Object.assign(roleForm, {
    name: role.name,
    description: role.description || ''
  })
  roleDialogVisible.value = true
}

// 提交角色表单
const handleRoleSubmit = async () => {
  if (!roleFormRef.value) return

  await roleFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEditing.value) {
          await updateRole(selectedRole.value.id, roleForm)
          ElMessage.success('角色更新成功')
        } else {
          await createRole(roleForm)
          ElMessage.success('角色添加成功')
        }
        roleDialogVisible.value = false
        await fetchRoles()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error(isEditing.value ? '更新失败' : '添加失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 删除角色
const handleDelete = async (role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteRole(role.id)
    ElMessage.success('角色删除成功')
    await fetchRoles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 显示权限分配对话框
const showPermissionDialog = async (role) => {
  selectedRole.value = role
  selectedPermissionIds.value = role.permissions?.map(p => p.id) || []

  try {
    availablePermissions.value = await getPermissions()
    permissionDialogVisible.value = true
  } catch (error) {
    console.error('获取权限列表失败:', error)
    ElMessage.error('获取权限列表失败')
  }
}

// 分配权限
const handleAssignPermissions = async () => {
  permissionLoading.value = true
  try {
    await assignPermissions(selectedRole.value.id, selectedPermissionIds.value)
    ElMessage.success('权限分配成功')
    permissionDialogVisible.value = false
    await fetchRoles()
  } catch (error) {
    console.error('权限分配失败:', error)
    ElMessage.error('权限分配失败')
  } finally {
    permissionLoading.value = false
  }
}

onMounted(() => {
  fetchRoles()
})
</script>

<style scoped>
.roles-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.permission-info {
  margin-bottom: 10px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.permission-info p {
  margin: 0;
}

.permission-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.permission-checkbox {
  margin-bottom: 12px;
  width: 100%;
}

.permission-item {
  display: flex;
  flex-direction: column;
}

.permission-name {
  font-weight: 500;
}

.permission-code {
  font-size: 12px;
  color: #909399;
}
</style>
