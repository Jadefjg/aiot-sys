<template>
  <div class="firmware-container">
    <!-- 固件管理 -->
    <el-card class="firmware-card">
      <template #header>
        <div class="card-header">
          <span>固件管理</span>
          <el-button type="primary" @click="showUploadDialog">
            <el-icon><Upload /></el-icon>
            上传固件
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索固件版本或产品ID"
          style="width: 300px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 固件列表 -->
      <el-table :data="filteredFirmwares" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="version" label="版本号" width="120" />
        <el-table-column prop="product_id" label="产品ID" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="success"
              size="small"
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button type="primary" size="small" @click="showDetailDialog(row)">
              详情
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 升级任务列表 -->
    <el-card class="task-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>升级任务</span>
          <el-button type="primary" @click="fetchUpgradeTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table :data="upgradeTasks" style="width: 100%" v-loading="taskLoading" stripe>
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="device_id" label="设备ID" width="150" />
        <el-table-column prop="firmware_version" label="目标版本" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending' || row.status === 'in_progress'"
              type="danger"
              size="small"
              @click="handleCancelTask(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传固件对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传固件" width="500px">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="100px">
        <el-form-item label="版本号" prop="version">
          <el-input v-model="uploadForm.version" placeholder="请输入版本号，如 1.0.0" />
        </el-form-item>
        <el-form-item label="产品ID" prop="product_id">
          <el-input v-model="uploadForm.product_id" placeholder="请输入产品ID" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入固件描述"
          />
        </el-form-item>
        <el-form-item label="固件文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".bin,.hex,.fw"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">只能上传 .bin/.hex/.fw 文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploadLoading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 固件详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="固件详情" width="500px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="ID">{{ selectedFirmware?.id }}</el-descriptions-item>
        <el-descriptions-item label="版本号">{{ selectedFirmware?.version }}</el-descriptions-item>
        <el-descriptions-item label="产品ID">{{ selectedFirmware?.product_id }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ selectedFirmware?.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">{{ formatFileSize(selectedFirmware?.file_size) }}</el-descriptions-item>
        <el-descriptions-item label="文件路径">{{ selectedFirmware?.file_path }}</el-descriptions-item>
        <el-descriptions-item label="MD5校验">{{ selectedFirmware?.checksum || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="selectedFirmware?.is_active ? 'success' : 'info'">
            {{ selectedFirmware?.is_active ? '已激活' : '未激活' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="上传时间">{{ formatTime(selectedFirmware?.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getFirmwares,
  getFirmware,
  uploadFirmware,
  deleteFirmware,
  activateFirmware,
  getUpgradeTasks,
  cancelUpgradeTask
} from '@/api/modules/firmware'

// 状态
const loading = ref(false)
const taskLoading = ref(false)
const uploadLoading = ref(false)
const firmwares = ref([])
const upgradeTasks = ref([])
const searchKeyword = ref('')

// 对话框状态
const uploadDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedFirmware = ref(null)

// 上传表单
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const uploadFile = ref(null)
const uploadForm = reactive({
  version: '',
  product_id: '',
  description: ''
})

const uploadRules = {
  version: [
    { required: true, message: '请输入版本号', trigger: 'blur' }
  ],
  product_id: [
    { required: true, message: '请输入产品ID', trigger: 'blur' }
  ]
}

// 计算属性：过滤后的固件列表
const filteredFirmwares = computed(() => {
  if (!searchKeyword.value) return firmwares.value
  const keyword = searchKeyword.value.toLowerCase()
  return firmwares.value.filter(f =>
    f.version.toLowerCase().includes(keyword) ||
    f.product_id.toLowerCase().includes(keyword)
  )
})

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    in_progress: '进行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 获取固件列表
const fetchFirmwares = async () => {
  loading.value = true
  try {
    firmwares.value = await getFirmwares()
  } catch (error) {
    console.error('获取固件列表失败:', error)
    ElMessage.error('获取固件列表失败')
  } finally {
    loading.value = false
  }
}

// 获取升级任务列表
const fetchUpgradeTasks = async () => {
  taskLoading.value = true
  try {
    upgradeTasks.value = await getUpgradeTasks()
  } catch (error) {
    console.error('获取升级任务失败:', error)
    ElMessage.error('获取升级任务失败')
  } finally {
    taskLoading.value = false
  }
}

// 显示上传对话框
const showUploadDialog = () => {
  Object.assign(uploadForm, {
    version: '',
    product_id: '',
    description: ''
  })
  uploadFile.value = null
  uploadDialogVisible.value = true
}

// 文件改变
const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

// 文件移除
const handleFileRemove = () => {
  uploadFile.value = null
}

// 上传固件
const handleUpload = async () => {
  if (!uploadFormRef.value) return

  await uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!uploadFile.value) {
        ElMessage.warning('请选择固件文件')
        return
      }

      uploadLoading.value = true
      try {
        const formData = new FormData()
        formData.append('file', uploadFile.value)
        formData.append('version', uploadForm.version)
        formData.append('product_id', uploadForm.product_id)
        if (uploadForm.description) {
          formData.append('description', uploadForm.description)
        }

        await uploadFirmware(formData)
        ElMessage.success('固件上传成功')
        uploadDialogVisible.value = false
        await fetchFirmwares()
      } catch (error) {
        console.error('上传失败:', error)
        ElMessage.error('上传失败')
      } finally {
        uploadLoading.value = false
      }
    }
  })
}

// 激活固件
const handleActivate = async (firmware) => {
  try {
    await ElMessageBox.confirm(
      `确定要激活固件版本 "${firmware.version}" 吗？`,
      '激活确认',
      { type: 'warning' }
    )
    await activateFirmware(firmware.id)
    ElMessage.success('固件激活成功')
    await fetchFirmwares()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('激活失败:', error)
      ElMessage.error('激活失败')
    }
  }
}

// 删除固件
const handleDelete = async (firmware) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除固件版本 "${firmware.version}" 吗？`,
      '删除确认',
      { type: 'warning' }
    )
    await deleteFirmware(firmware.id)
    ElMessage.success('固件删除成功')
    await fetchFirmwares()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 显示详情对话框
const showDetailDialog = (firmware) => {
  selectedFirmware.value = firmware
  detailDialogVisible.value = true
}

// 取消升级任务
const handleCancelTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消该升级任务吗？',
      '取消确认',
      { type: 'warning' }
    )
    await cancelUpgradeTask(task.id)
    ElMessage.success('任务已取消')
    await fetchUpgradeTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
      ElMessage.error('取消失败')
    }
  }
}

onMounted(() => {
  fetchFirmwares()
  fetchUpgradeTasks()
})
</script>

<style scoped>
.firmware-container {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
}
</style>
