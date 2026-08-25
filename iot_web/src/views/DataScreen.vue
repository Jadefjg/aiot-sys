<template>
  <div class="screen-page" v-loading="loading">
    <div class="screen-header">
      <h1>IoT 数据大屏</h1>
      <div class="header-right">
        <span>{{ now }}</span>
        <el-button text @click="$router.push('/dashboard')">退出</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :span="4" v-for="k in kpis" :key="k.label">
        <div class="kpi">
          <div class="kpi-value">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <div class="panel map-panel">
          <div class="panel-title">设备分布</div>
          <div class="map-wrap">
            <IotMap :markers="mapMarkers" :show-track="false" height="360px" theme="dashboard" />
            <div v-if="!mapMarkers.length" class="map-empty">
              <span>暂无定位设备，请在设备详情中设置经纬度</span>
            </div>
            <div class="map-legend">
              <span><i class="dot online" />在线</span>
              <span><i class="dot offline" />离线</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="panel">
          <div class="panel-title">实时告警</div>
          <div v-if="!alarms.length" class="empty">暂无告警</div>
          <div v-for="a in alarms" :key="a.id" class="alarm-row">
            <span class="lvl">{{ a.level }}</span>
            <span class="ttl">{{ a.title }}</span>
            <span class="tm">{{ formatTime(a.created_at) }}</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="24">
        <div class="panel">
          <div class="panel-title">设备状态</div>
          <el-table :data="devices.slice(0, 12)" size="small" class="dark-table">
            <el-table-column prop="device_name" label="设备" />
            <el-table-column prop="product_id" label="产品" width="120" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <span :class="row.status === 'online' ? 'on' : 'off'">{{ row.status }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最新值" show-overflow-tooltip>
              <template #default="{ row }">{{ summarize(row.values) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getOverview } from '@/api/modules/overview'
import { getDevices, getOnlineDevices } from '@/api/modules/devices'
import { getProducts } from '@/api/modules/products'
import { getAlarms } from '@/api/modules/alarms'
import IotMap from '@/components/IotMap.vue'

const loading = ref(false)
const overview = ref(null)
const devices = ref([])
const online = ref([])
const products = ref([])
const alarms = ref([])
const now = ref('')
let timer = null
let clock = null

const kpis = computed(() => [
  { label: '设备总数', value: overview.value?.devices ?? devices.value.length },
  { label: '在线', value: overview.value?.online ?? online.value.length },
  { label: '离线', value: overview.value?.offline ?? devices.value.filter((d) => d.status !== 'online').length },
  { label: '异常', value: overview.value?.errors ?? devices.value.filter((d) => d.error).length },
  { label: '产品', value: overview.value?.products ?? products.value.length },
  { label: '未确认告警', value: alarms.value.length },
])

const mapMarkers = computed(() =>
  devices.value
    .filter((d) => d.latitude != null && d.longitude != null)
    .map((d) => ({
      latitude: d.latitude,
      longitude: d.longitude,
      device_id: d.device_id,
      device_name: d.device_name,
      status: d.status,
      error: d.error,
      label: `${d.device_name} (${d.status})`,
    }))
)

const summarize = (values) => {
  if (!values || !Object.keys(values).length) return '-'
  return Object.entries(values).slice(0, 3).map(([k, v]) => `${k}:${v}`).join(' ')
}
const formatTime = (t) => (t ? new Date(t).toLocaleTimeString('zh-CN') : '-')

const refresh = async () => {
  loading.value = true
  try {
    const [ov, devs, on, prods, als] = await Promise.all([
      getOverview().catch(() => null),
      getDevices().catch(() => []),
      getOnlineDevices().catch(() => []),
      getProducts().catch(() => []),
      getAlarms({ acknowledged: false, limit: 20 }).catch(() => []),
    ])
    overview.value = ov
    devices.value = Array.isArray(devs) ? devs : (devs?.devices || [])
    online.value = Array.isArray(on) ? on : []
    products.value = Array.isArray(prods) ? prods : []
    alarms.value = Array.isArray(als) ? als : []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, 15000)
  clock = setInterval(() => {
    now.value = new Date().toLocaleString('zh-CN')
  }, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
  clearInterval(clock)
})
</script>

<style scoped>
.screen-page {
  min-height: 100vh;
  padding: 20px 24px;
  background: #0b1220;
  color: #e2e8f0;
}
.screen-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}
.screen-header h1 {
  margin: 0; font-size: 22px; letter-spacing: 2px; color: #93c5fd;
}
.header-right { display: flex; align-items: center; gap: 16px; color: #94a3b8; }
.kpi {
  background: #111827; border: 1px solid #1e293b; border-radius: 8px;
  padding: 16px; text-align: center;
}
.kpi-value { font-size: 28px; font-weight: 700; color: #60a5fa; }
.kpi-label { margin-top: 6px; font-size: 13px; color: #94a3b8; }
.panel {
  background: #111827; border: 1px solid #1e293b; border-radius: 8px;
  padding: 14px; min-height: 360px;
}
.panel-title { font-size: 15px; margin-bottom: 12px; color: #93c5fd; }
.map-panel { min-height: 400px; }
.map-wrap { position: relative; }
.map-empty {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  padding: 10px 16px;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid #334155;
  color: #94a3b8;
  font-size: 13px;
  pointer-events: none;
  z-index: 500;
}
.map-legend {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 500;
  display: flex;
  gap: 14px;
  padding: 6px 12px;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid #334155;
  font-size: 12px;
  color: #cbd5e1;
}
.map-legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.map-legend .dot.online { background: #22c55e; box-shadow: 0 0 6px rgba(34, 197, 94, 0.6); }
.map-legend .dot.offline { background: #64748b; }
.dark-table { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: #0f172a; --el-table-text-color: #cbd5e1; --el-table-header-text-color: #94a3b8; --el-table-border-color: #1e293b; --el-table-row-hover-bg-color: #1e293b; }
.on { color: #4ade80; }
.off { color: #94a3b8; }
.alarm-row {
  display: grid; grid-template-columns: 70px 1fr 80px; gap: 8px;
  padding: 8px 0; border-bottom: 1px solid #1e293b; font-size: 13px;
}
.lvl { color: #fbbf24; }
.ttl { color: #e2e8f0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tm { color: #64748b; text-align: right; }
.empty { color: #64748b; padding: 24px 0; text-align: center; }
</style>
