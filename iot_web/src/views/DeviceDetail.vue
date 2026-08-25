<template>
  <div class="device-detail" v-loading="loading">
    <el-page-header @back="$router.push('/devices')">
      <template #content>
        <span>{{ device?.device_name || deviceId }}</span>
        <el-tag v-if="device" :type="device.status === 'online' ? 'success' : 'info'" size="small" style="margin-left: 8px">
          {{ device.status }}
        </el-tag>
        <el-tag v-if="device?.error" type="danger" size="small" style="margin-left: 6px">故障</el-tag>
      </template>
    </el-page-header>

    <el-card style="margin-top: 16px" v-if="device">
      <el-descriptions :column="3" size="small" border>
        <el-descriptions-item label="设备ID">{{ device.device_id }}</el-descriptions-item>
        <el-descriptions-item label="产品">
          <el-button link type="primary" @click="$router.push(`/products/${device.product_id}`)">
            {{ device.product_id }}
          </el-button>
        </el-descriptions-item>
        <el-descriptions-item label="网关">{{ device.gateway_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="固件">{{ device.firmware_version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="位置">
          {{ device.latitude != null ? `${device.latitude}, ${device.longitude}` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="故障信息">{{ device.error_string || '无' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-result v-if="loadError && !device" icon="warning" title="设备不存在或加载失败">
      <template #extra>
        <el-button type="primary" @click="$router.push('/devices')">返回设备列表</el-button>
      </template>
    </el-result>

    <el-card style="margin-top: 16px" v-if="device">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <!-- 实时数据 -->
        <el-tab-pane label="实时数据" name="values">
          <div class="tab-toolbar">
            <el-button size="small" @click="refreshValues">刷新</el-button>
            <el-button size="small" type="primary" :loading="ctrlLoading" @click="doSync">采集同步</el-button>
            <span class="hint">HTTP 拉取最新快照；也可扩展 MQTT 订阅 device/{id}/values</span>
          </div>
          <el-empty v-if="!Object.keys(values).length" description="暂无属性，可在「模拟上报」写入" />
          <el-row :gutter="12" v-else>
            <el-col :span="8" v-for="(val, key) in values" :key="key" style="margin-bottom: 12px">
              <div class="value-card">
                <div class="value-label">{{ propLabel(key) }}</div>
                <div class="value-num">{{ val }} <small>{{ propUnit(key) }}</small></div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 操作：写/读/动作 -->
        <el-tab-pane v-if="canOperate" label="远程操作" name="actions">
          <el-tabs type="border-card">
            <el-tab-pane label="写属性">
              <el-form label-width="100px" style="max-width: 520px">
                <el-form-item v-for="p in writableProps" :key="p.name" :label="p.label || p.name">
                  <el-input v-model="writeForm[p.name]" :placeholder="p.unit || ''" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="ctrlLoading" @click="doWrite">下发写入</el-button>
                </el-form-item>
              </el-form>
              <el-alert v-if="!writableProps.length" type="info" :closable="false" title="物模型无可写属性（mode 含 w）" />
            </el-tab-pane>
            <el-tab-pane label="读属性">
              <el-select v-model="readPoints" multiple placeholder="选择测点" style="width: 360px">
                <el-option v-for="p in properties" :key="p.name" :label="p.label || p.name" :value="p.name" />
              </el-select>
              <el-button type="primary" style="margin-left: 8px" :loading="ctrlLoading" @click="doRead">读取</el-button>
            </el-tab-pane>
            <el-tab-pane label="动作">
              <el-space wrap>
                <el-button
                  v-for="a in actions"
                  :key="a.name"
                  type="warning"
                  :loading="ctrlLoading"
                  @click="doAction(a.name)"
                >{{ a.label || a.name }}</el-button>
              </el-space>
              <el-alert v-if="!actions.length" type="info" :closable="false" title="物模型未定义动作" style="margin-top: 8px" />
            </el-tab-pane>
            <el-tab-pane label="模拟上报">
              <el-input v-model="simJson" type="textarea" :rows="4" />
              <el-button type="success" style="margin-top: 8px" @click="doSimulate">上报并评估告警</el-button>
            </el-tab-pane>
            <el-tab-pane label="电表拉合闸">
              <el-alert type="info" :closable="false" title="对齐 DGIoT DL/T645 电表控制，经连接通道下发拉闸/合闸" style="margin-bottom: 12px" />
              <el-form label-width="90px" style="max-width: 420px">
                <el-form-item label="表地址">
                  <el-input v-model="meterAddress" placeholder="设备元数据 address / meter" />
                </el-form-item>
                <el-form-item>
                  <el-button type="success" :loading="ctrlLoading" @click="doMeter(true)">合闸</el-button>
                  <el-button type="danger" :loading="ctrlLoading" @click="doMeter(false)">拉闸</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
          <pre v-if="lastResponse" class="resp">{{ lastResponse }}</pre>
        </el-tab-pane>

        <!-- 历史 -->
        <el-tab-pane label="历史曲线" name="history">
          <div class="tab-toolbar">
            <el-radio-group v-model="historyHours" size="small" @change="loadHistory">
              <el-radio-button :label="1">1小时</el-radio-button>
              <el-radio-button :label="24">24小时</el-radio-button>
              <el-radio-button :label="168">7天</el-radio-button>
            </el-radio-group>
            <el-tag size="small" :type="historySource === 'influx' ? 'success' : 'info'">
              {{ historySource === 'influx' ? 'InfluxDB' : historySource === 'mysql' ? 'MySQL 回退' : '—' }}
            </el-tag>
          </div>
          <div ref="chartRef" class="chart-box" v-show="historyPoints.length && chartReady" />
          <el-alert
            v-if="historyPoints.length && !chartReady"
            type="info"
            :closable="false"
            title="未安装 echarts 时仅展示下方历史表格；可执行 npm install echarts"
            style="margin-bottom: 8px"
          />
          <el-empty v-if="!historyPoints.length && !history.length" description="暂无历史数据" />
          <el-table :data="history" size="small" max-height="280" style="margin-top: 12px">
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
            </el-table-column>
            <el-table-column prop="data_type" label="类型" width="100" />
            <el-table-column label="数据">
              <template #default="{ row }">{{ JSON.stringify(row.data) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane v-if="canAdmin" label="授权" name="acl">
          <AclPanel
            :items="aclItems"
            :users="aclUsers"
            :can-admin="canAdmin"
            @grant="onGrantAcl"
            @revoke="onRevokeAcl"
          />
        </el-tab-pane>
        <!-- 设备影子 -->
        <el-tab-pane label="设备影子" name="shadow">
          <div class="tab-toolbar">
            <el-button size="small" @click="loadShadow">刷新</el-button>
            <el-button size="small" type="primary" :loading="ctrlLoading" :disabled="!canOperate" @click="saveShadow">下发期望状态</el-button>
            <span class="hint">reported 为上报快照，desired 经 MQTT setting 同步到设备</span>
          </div>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="shadow-title">Reported v{{ shadow.version || 0 }}</div>
              <pre class="resp">{{ JSON.stringify(shadow.reported || {}, null, 2) }}</pre>
            </el-col>
            <el-col :span="12">
              <div class="shadow-title">Desired</div>
              <el-input v-model="desiredJson" type="textarea" :rows="10" />
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 告警 -->
        <el-tab-pane label="告警" name="alarms">
          <el-table :data="deviceAlarms" size="small" v-loading="alarmLoading">
            <el-table-column prop="created_at" label="时间" width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="level" label="级别" width="90" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="message" label="消息" show-overflow-tooltip />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">{{ row.acknowledged ? '已确认' : '未确认' }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 轨迹 -->
        <el-tab-pane label="轨迹" name="track">
          <div class="tab-toolbar">
            <el-button size="small" @click="loadTrack">刷新轨迹</el-button>
            <span class="hint">基于 MQTT location 上报与定位历史</span>
          </div>
          <IotMap :points="trackPoints" height="420px" v-loading="trackLoading" />
          <el-table :data="trackPoints.slice().reverse()" size="small" max-height="200" style="margin-top: 12px">
            <el-table-column label="时间" width="180">
              <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
            </el-table-column>
            <el-table-column prop="latitude" label="纬度" width="120" />
            <el-table-column prop="longitude" label="经度" width="120" />
            <el-table-column prop="geo_code" label="区域码" />
          </el-table>
          <el-empty v-if="!trackPoints.length && !trackLoading" description="暂无轨迹，设备上报 location 后将自动记录" />
        </el-tab-pane>

        <!-- 子设备（网关视角） -->
        <el-tab-pane v-if="isGateway || children.length" label="子设备" name="children">
          <el-table :data="children" size="small">
            <el-table-column prop="device_id" label="设备ID" />
            <el-table-column prop="device_name" label="名称" />
            <el-table-column prop="status" label="状态" width="90" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="primary" @click="$router.push(`/devices/${row.device_id}`)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!children.length" description="暂无挂载子设备" />
        </el-tab-pane>

        <!-- 网关侧场景 -->
        <el-tab-pane v-if="isGateway" label="网关场景" name="scenes">
          <el-button type="primary" size="small" @click="$router.push({ path: '/scenes', query: { gateway_id: deviceId } })">
            管理场景 / 定时
          </el-button>
          <el-button size="small" :loading="dlLoading" @click="downloadConfig('scene')">下载场景到网关</el-button>
          <el-button size="small" :loading="dlLoading" @click="downloadConfig('job')">下载定时</el-button>
          <el-button size="small" :loading="dlLoading" @click="downloadConfig('binding')">下载联动</el-button>
          <el-button size="small" :loading="dlLoading" @click="downloadConfig('script')">下载脚本</el-button>
          <el-table :data="gatewayScenes" size="small" style="margin-top: 12px">
            <el-table-column prop="name" label="场景" />
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">{{ row.enabled ? '是' : '否' }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getDevice, getDeviceValues, getDeviceData, getDevices, getDeviceTrack, getDeviceHistory,
  syncDevice, readDevice, writeDevice, invokeAction, putDeviceValues, downloadGatewayConfig,
  getDeviceShadow, setDeviceShadow, meterSwitch
} from '@/api/modules/devices'
import IotMap from '@/components/IotMap.vue'
import { useAuthStore } from '@/store/modules/auth'
import AclPanel from '@/components/AclPanel.vue'
import {
  getDeviceAcl, grantDeviceAcl, revokeDeviceAcl, getAclUsers
} from '@/api/modules/acl'
import { getProduct } from '@/api/modules/products'
import { getAlarms } from '@/api/modules/alarms'
import { getScenes } from '@/api/modules/scenes'

const route = useRoute()
const deviceId = route.params.deviceId
const loading = ref(false)
const loadError = ref(false)
const ctrlLoading = ref(false)
const alarmLoading = ref(false)
const activeTab = ref('values')
const device = ref(null)
const product = ref(null)
const values = ref({})
const authStore = useAuthStore()
const history = ref([])
const historySource = ref('')
const historyHours = ref(24)
const myRole = ref(null)
const aclItems = ref([])
const aclUsers = ref([])
const deviceAlarms = ref([])
const children = ref([])
const gatewayScenes = ref([])
const trackPoints = ref([])
const trackLoading = ref(false)
const dlLoading = ref(false)
const writeForm = reactive({})
const readPoints = ref([])
const simJson = ref('{"temperature": 36.5}')
const lastResponse = ref('')
const shadow = ref({ reported: {}, desired: {}, version: 0 })
const desiredJson = ref('{}')
const meterAddress = ref('')
const chartRef = ref(null)
const chartReady = ref(false)
let chartInst = null
let echartsLib = null

const properties = computed(() => product.value?.model?.properties || [])
const actions = computed(() => product.value?.model?.actions || [])
const writableProps = computed(() =>
  properties.value.filter((p) => (p.mode || 'r').includes('w'))
)
const isGateway = computed(() => !!product.value?.is_gateway || children.value.length > 0)
const canOperate = computed(() => authStore.isSuperuser || ['operator', 'admin'].includes(myRole.value))
const canAdmin = computed(() => authStore.isSuperuser || myRole.value === 'admin')

const historyPoints = computed(() => {
  const series = {}
  history.value.slice().reverse().forEach((row) => {
    const data = row.data || {}
    Object.keys(data).forEach((k) => {
      if (typeof data[k] !== 'number') return
      if (!series[k]) series[k] = []
      series[k].push([row.timestamp, data[k]])
    })
  })
  return Object.entries(series)
})

const propLabel = (key) => properties.value.find((p) => p.name === key)?.label || key
const propUnit = (key) => properties.value.find((p) => p.name === key)?.unit || ''
const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN') : '-')

const loadEcharts = async () => {
  if (echartsLib) return echartsLib
  try {
    echartsLib = await import('echarts')
    chartReady.value = true
    return echartsLib
  } catch {
    chartReady.value = false
    return null
  }
}

const renderChart = async () => {
  await nextTick()
  if (!chartRef.value || !historyPoints.value.length) return
  const echarts = await loadEcharts()
  if (!echarts) return
  if (!chartInst) chartInst = echarts.init(chartRef.value)
  chartInst.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: historyPoints.value.map(([k]) => k) },
    grid: { left: 40, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'time' },
    yAxis: { type: 'value' },
    series: historyPoints.value.map(([name, data]) => ({
      name, type: 'line', showSymbol: false, data
    }))
  })
}

const loadHistory = async () => {
  try {
    const start = new Date(Date.now() - historyHours.value * 3600 * 1000).toISOString()
    const hist = await getDeviceHistory(deviceId, { limit: 500, start })
    historySource.value = hist?.source || ''
    if (hist?.series) {
      history.value = Object.entries(hist.series).flatMap(([key, pts]) =>
        (pts || []).map(([timestamp, value]) => ({ timestamp, data_type: 'property', data: { [key]: value } }))
      )
    }
  } catch {
    historySource.value = 'mysql'
  }
}

const loadAcl = async () => {
  try {
    const data = await getDeviceAcl(deviceId)
    myRole.value = data.my_role
    aclItems.value = data.items || []
    if (canAdmin.value) aclUsers.value = await getAclUsers().catch(() => [])
  } catch {
    myRole.value = authStore.deviceRole(deviceId, device.value?.product_id)
  }
}

const onGrantAcl = async (body) => {
  await grantDeviceAcl(deviceId, body)
  ElMessage.success('已授权')
  loadAcl()
}

const onRevokeAcl = async (userId) => {
  await revokeDeviceAcl(deviceId, userId)
  loadAcl()
}

const load = async () => {
  loading.value = true
  loadError.value = false
  try {
    device.value = await getDevice(deviceId)
    const vals = await getDeviceValues(deviceId)
    values.value = vals.values || {}
    history.value = await getDeviceData(deviceId, { limit: 100 })
    await loadHistory()
    await loadAcl()
    try {
      product.value = await getProduct(device.value.product_id)
      writableProps.value.forEach((p) => {
        if (writeForm[p.name] === undefined) writeForm[p.name] = values.value[p.name] ?? ''
      })
    } catch {
      product.value = null
    }
    const all = await getDevices({ gateway_id: deviceId }).catch(() => [])
    const list = Array.isArray(all) ? all : (all?.devices || [])
    children.value = list.filter((d) => d.gateway_id === deviceId)
    const meta = device.value?.device_metadata || {}
    meterAddress.value = meta.address || meta.meter || ''
  } catch {
    loadError.value = true
    device.value = null
  } finally {
    loading.value = false
  }
}

const refreshValues = async () => {
  const vals = await getDeviceValues(deviceId)
  values.value = vals.values || {}
}

const loadAlarms = async () => {
  alarmLoading.value = true
  try {
    deviceAlarms.value = await getAlarms({ device_id: deviceId, limit: 50 })
  } finally {
    alarmLoading.value = false
  }
}

const loadGatewayScenes = async () => {
  gatewayScenes.value = await getScenes({ gateway_id: deviceId }).catch(() => [])
}

const downloadConfig = async (database) => {
  dlLoading.value = true
  try {
    const res = await downloadGatewayConfig(deviceId, database)
    ElMessage.success(`已下发 ${database} (${res.count || 0} 条) → ${res.topic}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '下发失败')
  } finally {
    dlLoading.value = false
  }
}

const loadTrack = async () => {
  trackLoading.value = true
  try {
    const res = await getDeviceTrack(deviceId)
    trackPoints.value = res.points || []
  } catch {
    trackPoints.value = []
  } finally {
    trackLoading.value = false
  }
}

const loadShadow = async () => {
  shadow.value = await getDeviceShadow(deviceId).catch(() => ({ reported: {}, desired: {}, version: 0 }))
  desiredJson.value = JSON.stringify(shadow.value.desired || {}, null, 2)
}

const saveShadow = async () => {
  ctrlLoading.value = true
  try {
    const desired = JSON.parse(desiredJson.value || '{}')
    shadow.value = await setDeviceShadow(deviceId, desired)
    ElMessage.success('期望状态已下发')
  } catch (e) {
    ElMessage.error(e.message || e.response?.data?.detail || '影子更新失败')
  } finally {
    ctrlLoading.value = false
  }
}

const doMeter = async (close) => {
  ctrlLoading.value = true
  try {
    showResp(await meterSwitch(deviceId, { close, address: meterAddress.value || undefined }))
    ElMessage.success(close ? '合闸指令已下发' : '拉闸指令已下发')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '电表控制失败')
  } finally {
    ctrlLoading.value = false
  }
}

const onTabChange = (name) => {
  if (name === 'history') renderChart()
  if (name === 'alarms') loadAlarms()
  if (name === 'scenes') loadGatewayScenes()
  if (name === 'track') loadTrack()
  if (name === 'shadow') loadShadow()
}

const showResp = (data) => { lastResponse.value = JSON.stringify(data, null, 2) }

const doSync = async () => {
  ctrlLoading.value = true
  try {
    showResp(await syncDevice(deviceId))
    ElMessage.success('同步完成')
    await refreshValues()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '同步失败')
  } finally {
    ctrlLoading.value = false
  }
}

const doWrite = async () => {
  const payload = {}
  writableProps.value.forEach((p) => {
    let v = writeForm[p.name]
    if (v === '' || v === undefined) return
    if (p.type === 'number') v = Number(v)
    payload[p.name] = v
  })
  ctrlLoading.value = true
  try {
    showResp(await writeDevice(deviceId, payload))
    ElMessage.success('写入已下发')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '写入失败')
  } finally {
    ctrlLoading.value = false
  }
}

const doRead = async () => {
  ctrlLoading.value = true
  try {
    showResp(await readDevice(deviceId, readPoints.value))
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '读取失败')
  } finally {
    ctrlLoading.value = false
  }
}

const doAction = async (name) => {
  ctrlLoading.value = true
  try {
    showResp(await invokeAction(deviceId, name))
    ElMessage.success(`动作 ${name} 已执行`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '动作失败')
  } finally {
    ctrlLoading.value = false
  }
}

const doSimulate = async () => {
  try {
    const data = JSON.parse(simJson.value)
    await putDeviceValues(deviceId, data)
    ElMessage.success('已上报')
    await load()
  } catch (e) {
    ElMessage.error(e.message || 'JSON 无效')
  }
}

watch(historyPoints, () => {
  if (activeTab.value === 'history') renderChart()
})

onMounted(load)
</script>

<style scoped>
.tab-toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.hint { font-size: 12px; color: #909399; margin-left: 8px; }
.value-card {
  background: #f5f7fa; border-radius: 8px; padding: 14px 16px;
}
.value-label { font-size: 13px; color: #909399; }
.value-num { font-size: 22px; font-weight: 700; color: #303133; margin-top: 6px; }
.value-num small { font-size: 12px; font-weight: 400; color: #909399; }
.chart-box { width: 100%; height: 280px; }
.resp {
  margin-top: 12px; background: #0f172a; color: #e2e8f0;
  padding: 12px; border-radius: 6px; font-size: 12px; max-height: 200px; overflow: auto;
}
.shadow-title { font-size: 13px; color: #606266; margin-bottom: 6px; }
</style>
