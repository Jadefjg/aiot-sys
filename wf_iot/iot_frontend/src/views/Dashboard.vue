<template>
  <div class="dashboard-container">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon device-icon">
              <el-icon :size="32"><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalDevices }}</div>
              <div class="stat-label">设备总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon online-icon">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.onlineDevices }}</div>
              <div class="stat-label">在线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon user-icon">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalUsers }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon firmware-icon">
              <el-icon :size="32"><Upload /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalFirmware }}</div>
              <div class="stat-label">固件版本</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="16">
        <el-card class="recent-devices-card">
          <template #header>
            <div class="card-header">
              <span>最近设备活动</span>
              <el-button type="primary" link @click="$router.push('/devices')">
                查看全部
              </el-button>
            </div>
          </template>
          <el-table :data="recentDevices" style="width: 100%" v-loading="loading">
            <el-table-column prop="device_id" label="设备ID" width="180" />
            <el-table-column prop="device_name" label="设备名称" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'online' ? 'success' : 'info'">
                  {{ row.status === 'online' ? '在线' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="firmware_version" label="固件版本" width="120" />
            <el-table-column prop="last_online_at" label="最后活动" width="180">
              <template #default="{ row }">
                {{ formatTime(row.last_online_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="quick-actions-card">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/devices')">
              <el-icon><Cpu /></el-icon>
              设备管理
            </el-button>
            <el-button type="success" @click="$router.push('/firmware')">
              <el-icon><Upload /></el-icon>
              固件升级
            </el-button>
            <el-button type="warning" @click="$router.push('/users')">
              <el-icon><User /></el-icon>
              用户管理
            </el-button>
            <el-button type="info" @click="$router.push('/roles')">
              <el-icon><UserFilled /></el-icon>
              角色管理
            </el-button>
          </div>
        </el-card>

        <el-card class="system-info-card" style="margin-top: 20px">
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="info-label">系统状态</span>
              <el-tag type="success">正常运行</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">MQTT连接</span>
              <el-tag type="success">已连接</el-tag>
            </div>
            <div class="info-item">
              <span class="info-label">数据库</span>
              <el-tag type="success">正常</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDevices, getOnlineDevices } from '@/api/modules/devices'
import { getUsers } from '@/api/modules/users'
import { getFirmwares } from '@/api/modules/firmware'

const loading = ref(false)
const stats = ref({
  totalDevices: 0,
  onlineDevices: 0,
  totalUsers: 0,
  totalFirmware: 0
})
const recentDevices = ref([])

// 格式化时间
const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

// 获取统计数据
const fetchStats = async () => {
  loading.value = true
  try {
    // 并行获取所有数据
    const [devices, onlineDevices, users, firmwares] = await Promise.all([
      getDevices().catch(() => []),
      getOnlineDevices().catch(() => []),
      getUsers().catch(() => []),
      getFirmwares().catch(() => [])
    ])

    stats.value = {
      totalDevices: devices.length,
      onlineDevices: onlineDevices.length,
      totalUsers: users.length,
      totalFirmware: firmwares.length
    }

    // 取最近5个设备显示
    recentDevices.value = devices.slice(0, 5)
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard-container {
  padding: 0;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.device-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.online-icon {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.user-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.firmware-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.content-row {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-actions .el-button {
  justify-content: flex-start;
  width: 100%;
}

.system-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #666;
}
</style>
