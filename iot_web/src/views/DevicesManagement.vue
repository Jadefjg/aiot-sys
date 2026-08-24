<template>
  <div class="devices-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索设备ID或名称"
          style="width: 300px"
          clearable
          @clear="fetchDevices"
          @keyup.enter="fetchDevices"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 150px; margin-left: 10px">
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-button type="primary" @click="fetchDevices" style="margin-left: 10px">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>

      <!-- 设备列表表格 -->
      <el-table :data="filteredDevices" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="device_id" label="设备ID" width="180" />
        <el-table-column prop="device_name" label="设备名称" />
        <el-table-column prop="product_id" label="产品ID" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="firmware_version" label="固件版本" width="120">
          <template #default="{ row }">
            {{ row.firmware_version || 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column prop="last_online_at" label="最后活动" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_online_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" @click="showControlDialog(row)">
              控制
            </el-button>
            <el-button type="warning" size="small" @click="showUpgradeDialog(row)">
              升级
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑设备对话框 -->
    <el-dialog
      v-model="deviceDialogVisible"
      :title="isEditing ? '编辑设备' : '添加设备'"
      width="500px"
    >
      <el-form ref="deviceFormRef" :model="deviceForm" :rules="deviceRules" label-width="100px">
        <el-form-item label="设备ID" prop="device_id">
          <el-input v-model="deviceForm.device_id" :disabled="isEditing" placeholder="请输入设备唯一ID" />
        </el-form-item>
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="deviceForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="产品ID" prop="product_id">
          <el-input v-model="deviceForm.product_id" placeholder="请输入产品ID" />
        </el-form-item>
        <el-form-item label="设备密钥" prop="device_secret" v-if="!isEditing">
          <el-input v-model="deviceForm.device_secret" placeholder="请输入设备密钥" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deviceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDeviceSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 设备控制对话框 -->
    <el-dialog v-model="controlDialogVisible" title="设备控制" width="500px">
      <div class="control-info">
        <p><strong>设备ID:</strong> {{ selectedDevice?.device_id }}</p>
        <p><strong>设备名称:</strong> {{ selectedDevice?.device_name }}</p>
      </div>
      <el-form label-width="100px">
        <el-form-item label="控制命令">
          <el-input
            v-model="commandJson"
            type="textarea"
            :rows="4"
            placeholder='请输入JSON格式命令，如：{"light": "on", "brightness": 80}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="controlDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSendCommand" :loading="controlLoading">
          发送命令
        </el-button>
      </template>
    </el-dialog>

    <!-- 固件升级对话框 -->
    <el-dialog v-model="upgradeDialogVisible" title="固件升级" width="500px">
      <div class="upgrade-info">
        <p><strong>设备:</strong> {{ selectedDevice?.device_name }}</p>
        <p><strong>当前版本:</strong> {{ selectedDevice?.firmware_version || 'N/A' }}</p>
      </div>
      <el-form label-width="100px">
        <el-form-item label="目标固件">
          <el-select v-model="selectedFirmwareId" placeholder="请选择固件版本" style="width: 100%">
            <el-option
              v-for="fw in availableFirmwares"
              :key="fw.id"
              :label="`${fw.version} (${fw.product_id})`"
              :value="fw.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="upgradeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpgrade" :loading="upgradeLoading">
          开始升级
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDevices, getDevice, createDevice, updateDevice, deleteDevice, sendCommand } from '@/api/modules/devices'
import { getFirmwares, createUpgradeTask } from '@/api/modules/firmware'

// 状态
const loading = ref(false)
const submitLoading = ref(false)
const controlLoading = ref(false)
const upgradeLoading = ref(false)
const devices = ref([])
const searchKeyword = ref('')
const statusFilter = ref('')

// 对话框状态
const deviceDialogVisible = ref(false)
const controlDialogVisible = ref(false)
const upgradeDialogVisible = ref(false)
const isEditing = ref(false)
const selectedDevice = ref(null)
const commandJson = ref('')
const selectedFirmwareId = ref(null)
const availableFirmwares = ref([])

// 表单
const deviceFormRef = ref(null)
const deviceForm = reactive({
  device_id: '',
  device_name: '',
  product_id: '',
  device_secret: ''
})

const deviceRules = {
  device_id: [
    { required: true, message: '请输入设备ID', trigger: 'blur' }
  ],
  device_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  product_id: [
    { required: true, message: '请输入产品ID', trigger: 'blur' }
  ]
}

// 计算属性：过滤后的设备列表
const filteredDevices = computed(() => {
  let result = devices.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(d =>
      d.device_id.toLowerCase().includes(keyword) ||
      (d.device_name && d.device_name.toLowerCase().includes(keyword))
    )
  }
  if (statusFilter.value) {
    result = result.filter(d => d.status === statusFilter.value)
  }
  return result
})

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取设备列表
const fetchDevices = async () => {
  loading.value = true
  try {
    devices.value = await getDevices()
  } catch (error) {
    console.error('获取设备列表失败:', error)
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEditing.value = false
  Object.assign(deviceForm, {
    device_id: '',
    device_name: '',
    product_id: '',
    device_secret: ''
  })
  deviceDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (device) => {
  isEditing.value = true
  selectedDevice.value = device
  Object.assign(deviceForm, {
    device_id: device.device_id,
    device_name: device.device_name,
    product_id: device.product_id,
    device_secret: ''
  })
  deviceDialogVisible.value = true
}

// 提交设备表单
const handleDeviceSubmit = async () => {
  if (!deviceFormRef.value) return

  await deviceFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEditing.value) {
          await updateDevice(selectedDevice.value.device_id, {
            device_name: deviceForm.device_name,
            product_id: deviceForm.product_id
          })
          ElMessage.success('设备更新成功')
        } else {
          await createDevice(deviceForm)
          ElMessage.success('设备添加成功')
        }
        deviceDialogVisible.value = false
        await fetchDevices()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error(isEditing.value ? '更新失败' : '添加失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 删除设备
const handleDelete = async (device) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 "${device.device_name}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteDevice(device.device_id)
    ElMessage.success('设备删除成功')
    await fetchDevices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 显示控制对话框
const showControlDialog = (device) => {
  selectedDevice.value = device
  commandJson.value = ''
  controlDialogVisible.value = true
}

// 发送控制命令
const handleSendCommand = async () => {
  if (!commandJson.value.trim()) {
    ElMessage.warning('请输入控制命令')
    return
  }

  try {
    const command = JSON.parse(commandJson.value)
    controlLoading.value = true
    await sendCommand(selectedDevice.value.device_id, command)
    ElMessage.success('命令发送成功')
    controlDialogVisible.value = false
  } catch (error) {
    if (error instanceof SyntaxError) {
      ElMessage.error('命令格式错误，请输入有效的JSON')
    } else {
      console.error('发送命令失败:', error)
      ElMessage.error('发送命令失败')
    }
  } finally {
    controlLoading.value = false
  }
}

// 显示升级对话框
const showUpgradeDialog = async (device) => {
  selectedDevice.value = device
  selectedFirmwareId.value = null

  try {
    // 获取该产品的可用固件
    const firmwares = await getFirmwares({ product_id: device.product_id })
    availableFirmwares.value = firmwares
    if (firmwares.length > 0) {
      selectedFirmwareId.value = firmwares[0].id
    }
    upgradeDialogVisible.value = true
  } catch (error) {
    console.error('获取固件列表失败:', error)
    ElMessage.error('获取固件列表失败')
  }
}

// 执行固件升级
const handleUpgrade = async () => {
  if (!selectedFirmwareId.value) {
    ElMessage.warning('请选择目标固件')
    return
  }

  upgradeLoading.value = true
  try {
    await createUpgradeTask({
      device_id: selectedDevice.value.id,
      firmware_id: selectedFirmwareId.value
    })
    ElMessage.success('升级任务已创建')
    upgradeDialogVisible.value = false
  } catch (error) {
    console.error('创建升级任务失败:', error)
    ElMessage.error('创建升级任务失败')
  } finally {
    upgradeLoading.value = false
  }
}

onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.devices-container {
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

.control-info,
.upgrade-info {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.control-info p,
.upgrade-info p {
  margin: 8px 0;
}
</style>
