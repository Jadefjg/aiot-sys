<template>
  <div class="scada" v-loading="loading">
    <div class="scada-bar">
      <span>组态监控</span>
      <el-select
        v-model="selectedProductId"
        filterable
        placeholder="选择产品"
        style="width: 260px"
        @change="onProductChange"
      >
        <el-option
          v-for="p in productOptions"
          :key="p.product_id"
          :label="`${p.label} (${p.deviceCount})`"
          :value="p.product_id"
        />
      </el-select>
      <el-button size="small" @click="refreshAll">刷新</el-button>
      <el-button size="small" type="primary" :disabled="!selectedProductId" @click="goDesign">编辑组态</el-button>
    </div>

    <el-alert
      v-if="missingProduct"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 12px"
      :title="`产品「${selectedProductId}」尚未创建，请在「产品物模型」中补充；当前按实时属性展示`"
    />

    <el-row :gutter="16">
      <el-col :span="6">
        <div class="device-panel">
          <div class="panel-title">设备列表</div>
          <el-empty v-if="!filteredDevices.length" description="该产品下暂无设备" :image-size="64" />
          <div
            v-for="d in filteredDevices"
            :key="d.device_id"
            class="device-item"
            :class="{ active: d.device_id === deviceId }"
            @click="selectDevice(d.device_id)"
          >
            <div class="device-name">{{ d.device_name || d.device_id }}</div>
            <div class="device-meta">
              <span>{{ d.device_id }}</span>
              <el-tag size="small" :type="d.status === 'online' ? 'success' : 'info'">
                {{ d.status || 'offline' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="18">
        <el-empty v-if="!deviceId" description="请选择左侧设备查看组态" />
        <div v-else-if="scadaWidgets.length" class="runtime-canvas" :style="canvasStyle">
          <div v-for="w in scadaWidgets" :key="w.id" class="rt-widget" :class="w.type" :style="widgetStyle(w)">
            <div class="rt-label">{{ w.label || w.prop }}</div>
            <div v-if="w.type === 'lamp'" class="rt-lamp" :class="{ on: truthy(values[w.prop]) }" />
            <el-switch v-else-if="w.type === 'switch'" :model-value="truthy(values[w.prop])" @change="(v) => doWrite(w.prop, v)" />
            <el-button v-else-if="w.type === 'button'" size="small" @click="doWrite(w.prop, 1)">下发</el-button>
            <div v-else class="rt-value">
              {{ formatValue(values[w.prop]) }}
              <small v-if="propUnit(w.prop)">{{ propUnit(w.prop) }}</small>
            </div>
            <div v-if="w.type === 'gauge'" class="rt-bar">
              <div class="rt-bar-fill" :style="{ width: gaugePct(w) + '%' }" />
            </div>
          </div>
        </div>
        <el-empty
          v-else-if="!displayProperties.length"
          description="该产品未配置物模型属性，且设备暂无实时数据"
        />
        <el-row :gutter="16" v-else>
          <el-col :span="6" v-for="p in displayProperties" :key="p.name">
            <div class="gauge">
              <div class="g-label">{{ p.label || p.name }}</div>
              <div class="g-value">
                {{ formatValue(values[p.name]) }}
                <small v-if="p.unit">{{ p.unit }}</small>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDevices, getDeviceValues, writeDevice } from '@/api/modules/devices'
import { getProducts } from '@/api/modules/products'

const router = useRouter()

const loading = ref(false)
const devices = ref([])
const products = ref([])
const selectedProductId = ref('')
const deviceId = ref('')
const values = ref({})
let timer = null

const productMap = computed(() => {
  const map = {}
  products.value.forEach((p) => {
    map[p.product_id] = p
  })
  return map
})

const productOptions = computed(() => {
  const counts = {}
  devices.value.forEach((d) => {
    const pid = d.product_id || '未绑定'
    counts[pid] = (counts[pid] || 0) + 1
  })
  const ids = new Set([
    ...products.value.map((p) => p.product_id),
    ...Object.keys(counts),
  ])
  return [...ids].filter(Boolean).map((product_id) => {
    const row = productMap.value[product_id]
    return {
      product_id,
      label: row?.name || product_id,
      deviceCount: counts[product_id] || 0,
    }
  })
})

const filteredDevices = computed(() =>
  devices.value.filter((d) => (d.product_id || '未绑定') === selectedProductId.value)
)

const currentProduct = computed(() => productMap.value[selectedProductId.value] || null)
const missingProduct = computed(() =>
  selectedProductId.value && !currentProduct.value && selectedProductId.value !== '未绑定'
)

const displayProperties = computed(() => {
  const props = currentProduct.value?.model?.properties || []
  if (props.length) return props
  return Object.keys(values.value).map((name) => ({
    name,
    label: name,
    unit: '',
  }))
})

const scadaWidgets = computed(() => currentProduct.value?.config?.scada?.widgets || [])
const canvasStyle = computed(() => {
  const scada = currentProduct.value?.config?.scada || {}
  return { width: (scada.width || 960) + 'px', height: (scada.height || 420) + 'px' }
})
const widgetStyle = (w) => ({ left: w.x + 'px', top: w.y + 'px', width: w.w + 'px', height: w.h + 'px' })
const truthy = (v) => v === true || v === 1 || v === '1' || v === 'true'
const propUnit = (name) => displayProperties.value.find((p) => p.name === name)?.unit || ''
const gaugePct = (w) => {
  const n = Number(values.value[w.prop])
  if (Number.isNaN(n)) return 0
  const min = Number(w.min || 0)
  const max = Number(w.max || 100) || 100
  return Math.max(0, Math.min(100, ((n - min) / (max - min)) * 100))
}
const goDesign = () => router.push({ path: '/scada/design', query: { productId: selectedProductId.value } })
const doWrite = async (prop, value) => {
  if (!deviceId.value || !prop) return
  try {
    await writeDevice(deviceId.value, { [prop]: value })
    ElMessage.success('已下发')
    loadDeviceValues()
  } catch {
    ElMessage.error('下发失败')
  }
}

const formatValue = (val) => {
  if (val == null || val === '') return '-'
  if (typeof val === 'object') return JSON.stringify(val)
  return val
}

const refreshAll = async () => {
  loading.value = true
  try {
    const [devRes, prodRes] = await Promise.all([
      getDevices().catch(() => []),
      getProducts().catch(() => []),
    ])
    devices.value = Array.isArray(devRes) ? devRes : (devRes?.devices || [])
    products.value = Array.isArray(prodRes) ? prodRes : []

    if (!selectedProductId.value && productOptions.value.length) {
      selectedProductId.value = productOptions.value[0].product_id
    }
    if (deviceId.value && !filteredDevices.value.some((d) => d.device_id === deviceId.value)) {
      deviceId.value = filteredDevices.value[0]?.device_id || ''
    }
    if (!deviceId.value && filteredDevices.value.length) {
      deviceId.value = filteredDevices.value[0].device_id
    }
    if (deviceId.value) {
      await loadDeviceValues()
    }
  } finally {
    loading.value = false
  }
}

const onProductChange = () => {
  deviceId.value = filteredDevices.value[0]?.device_id || ''
  values.value = {}
  if (deviceId.value) {
    loadDeviceValues()
  }
}

const selectDevice = (id) => {
  deviceId.value = id
  loadDeviceValues()
}

const loadDeviceValues = async () => {
  if (!deviceId.value) return
  try {
    const res = await getDeviceValues(deviceId.value)
    values.value = res?.values || {}
  } catch {
    values.value = {}
  }
}

onMounted(async () => {
  await refreshAll()
  timer = setInterval(() => {
    if (deviceId.value) loadDeviceValues()
  }, 5000)
})

onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.scada { min-height: 60vh; }
.scada-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}
.device-panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  min-height: 420px;
  padding: 12px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
}
.device-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  margin-bottom: 8px;
  background: #f5f7fa;
}
.device-item:hover { background: #ecf5ff; }
.device-item.active {
  background: #ecf5ff;
  border-color: #409eff;
}
.device-name { font-weight: 600; color: #303133; }
.device-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.gauge {
  background: linear-gradient(180deg, #1d4ed8 0%, #0f172a 100%);
  color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
.g-label { opacity: 0.8; font-size: 13px; }
.g-value { font-size: 28px; font-weight: 700; margin-top: 8px; }
.g-value small { font-size: 12px; font-weight: 400; }
.runtime-canvas {
  position: relative; background: #0f172a; border-radius: 8px; overflow: hidden;
  background-image: linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(90deg, #1e293b 1px, transparent 1px);
  background-size: 20px 20px;
}
.rt-widget {
  position: absolute; background: linear-gradient(180deg, #1d4ed8 0%, #0f172a 100%);
  color: #fff; border-radius: 8px; padding: 10px; box-sizing: border-box;
}
.rt-label { font-size: 12px; opacity: 0.85; }
.rt-value { font-size: 22px; font-weight: 700; margin-top: 6px; }
.rt-lamp { width: 18px; height: 18px; border-radius: 50%; background: #64748b; margin-top: 8px; }
.rt-lamp.on { background: #4ade80; box-shadow: 0 0 10px #4ade80; }
.rt-bar { height: 8px; background: #1e293b; border-radius: 4px; margin-top: 10px; overflow: hidden; }
.rt-bar-fill { height: 100%; background: #38bdf8; }
</style>
