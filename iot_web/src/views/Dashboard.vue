<template>
  <div class="dashboard-container">
    <el-row :gutter="16" class="stat-cards">
      <el-col :xs="12" :sm="8" :md="4" v-for="item in statCards" :key="item.label">
        <el-card shadow="hover" class="stat-card" @click="item.to && $router.push(item.to)">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: item.color }">
              <el-icon :size="28"><component :is="item.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近设备</span>
              <el-button type="primary" link @click="$router.push('/devices')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentDevices" v-loading="loading" stripe>
            <el-table-column prop="device_id" label="设备ID" width="160" />
            <el-table-column prop="device_name" label="名称" />
            <el-table-column prop="product_id" label="产品" width="120" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="statusType(row)" size="small">{{ statusText(row) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button link type="primary" @click="$router.push(`/devices/${row.device_id}`)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>未确认告警</span>
              <el-button type="primary" link @click="$router.push('/alarms')">告警中心</el-button>
            </div>
          </template>
          <el-empty v-if="!recentAlarms.length" description="暂无告警" :image-size="60" />
          <div v-for="a in recentAlarms" :key="a.id" class="alarm-item">
            <el-tag :type="a.level === 'error' ? 'danger' : 'warning'" size="small">{{ a.level }}</el-tag>
            <span class="alarm-title">{{ a.title }}</span>
          </div>
        </el-card>
        <el-card style="margin-top: 16px">
          <template #header><span>快捷入口</span></template>
          <div class="quick-actions">
            <el-button class="quick-btn" @click="$router.push('/products')">产品物模型</el-button>
            <el-button class="quick-btn" @click="$router.push('/devices')">设备管理</el-button>
            <el-button class="quick-btn" @click="$router.push('/scenes')">智能场景</el-button>
            <el-button class="quick-btn" @click="$router.push('/screen')">数据大屏</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getOverview } from '@/api/modules/overview'
import { getDevices, getOnlineDevices } from '@/api/modules/devices'
import { getProducts } from '@/api/modules/products'
import { getAlarms } from '@/api/modules/alarms'
import { getGroups } from '@/api/modules/groups'

const loading = ref(false)
const overview = ref(null)
const devices = ref([])
const onlineDevices = ref([])
const products = ref([])
const groups = ref([])
const recentAlarms = ref([])

const offlineCount = computed(() =>
  overview.value ? overview.value.offline : devices.value.filter((d) => d.status !== 'online').length
)
const errorCount = computed(() =>
  overview.value ? overview.value.errors : devices.value.filter((d) => d.error).length
)
const recentDevices = computed(() =>
  overview.value?.recent_devices?.length ? overview.value.recent_devices : devices.value.slice(0, 8)
)

const statCards = computed(() => [
  { label: '设备总数', value: overview.value?.devices ?? devices.value.length, icon: 'Cpu', color: '#409eff', to: '/devices' },
  { label: '在线', value: overview.value?.online ?? onlineDevices.value.length, icon: 'Connection', color: '#67c23a', to: '/devices' },
  { label: '离线', value: offlineCount.value, icon: 'Warning', color: '#909399', to: '/devices' },
  { label: '异常', value: errorCount.value, icon: 'CircleClose', color: '#f56c6c', to: '/alarms' },
  { label: '产品', value: overview.value?.products ?? products.value.length, icon: 'Box', color: '#e6a23c', to: '/products' },
  { label: '组织', value: overview.value?.groups ?? groups.value.length, icon: 'OfficeBuilding', color: '#909399', to: '/groups' },
])

const statusType = (row) => {
  if (row.error) return 'danger'
  return row.status === 'online' ? 'success' : 'info'
}
const statusText = (row) => {
  if (row.error) return '异常'
  return row.status === 'online' ? '在线' : '离线'
}

const fetchStats = async () => {
  loading.value = true
  try {
    const ov = await getOverview().catch(() => null)
    overview.value = ov
    if (ov) {
      recentAlarms.value = ov.recent_alarms || []
      return
    }
    const [devs, online, prods, gs, alarms] = await Promise.all([
      getDevices().catch(() => []),
      getOnlineDevices().catch(() => []),
      getProducts().catch(() => []),
      getGroups().catch(() => []),
      getAlarms({ acknowledged: false, limit: 8 }).catch(() => []),
    ])
    devices.value = Array.isArray(devs) ? devs : (devs?.devices || [])
    onlineDevices.value = Array.isArray(online) ? online : []
    products.value = Array.isArray(prods) ? prods : []
    groups.value = Array.isArray(gs) ? gs : []
    recentAlarms.value = Array.isArray(alarms) ? alarms.slice(0, 8) : []
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<style scoped>
.stat-cards { margin-bottom: 16px; }
.stat-card { margin-bottom: 12px; cursor: pointer; }
.stat-content { display: flex; align-items: center; gap: 12px; }
.stat-icon {
  width: 52px; height: 52px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; color: #fff;
}
.stat-value { font-size: 22px; font-weight: 700; color: #303133; }
.stat-label { font-size: 13px; color: #909399; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.alarm-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 0; border-bottom: 1px solid #f0f0f0;
}
.alarm-title { font-size: 13px; color: #606266; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.quick-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
}
.quick-actions .quick-btn {
  margin: 0;
  width: 100%;
  height: 40px;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
}
</style>
