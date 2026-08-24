<template>
  <div class="device-detail" v-loading="loading">
    <el-page-header @back="$router.push('/devices')" :content="`设备 ${deviceId}`" />

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card>
          <template #header>基本信息</template>
          <el-descriptions :column="1" size="small" v-if="device">
            <el-descriptions-item label="名称">{{ device.device_name }}</el-descriptions-item>
            <el-descriptions-item label="产品">{{ device.product_id }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="device.status === 'online' ? 'success' : 'info'">{{ device.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="网关">{{ device.gateway_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="故障">{{ device.error ? device.error_string : '无' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实时属性</span>
              <div>
                <el-button size="small" @click="refreshValues">刷新</el-button>
                <el-button size="small" type="primary" @click="doSync" :loading="ctrlLoading">同步</el-button>
              </div>
            </div>
          </template>
          <el-empty v-if="!Object.keys(values).length" description="暂无属性数据" />
          <el-descriptions v-else :column="2" border>
            <el-descriptions-item v-for="(val, key) in values" :key="key" :label="propLabel(key)">
              {{ val }} {{ propUnit(key) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>远程控制</template>
      <el-tabs>
        <el-tab-pane label="写属性">
          <el-form inline>
            <el-form-item v-for="p in writableProps" :key="p.name" :label="p.label || p.name">
              <el-input v-model="writeForm[p.name]" style="width: 140px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="ctrlLoading" @click="doWrite">下发写入</el-button>
            </el-form-item>
          </el-form>
          <el-alert v-if="!writableProps.length" type="info" title="请先在产品物模型中配置可写属性(mode 含 w)" :closable="false" />
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
          <el-alert v-if="!actions.length" type="info" title="物模型未定义动作" :closable="false" />
        </el-tab-pane>
        <el-tab-pane label="模拟上报">
          <el-input v-model="simJson" type="textarea" :rows="4" placeholder='{"temperature": 36.5}' />
          <el-button type="success" style="margin-top: 8px" @click="doSimulate">上报并评估告警</el-button>
        </el-tab-pane>
      </el-tabs>
      <pre v-if="lastResponse" class="resp">{{ lastResponse }}</pre>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>历史数据</template>
      <el-table :data="history" size="small" max-height="320">
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="data_type" label="类型" width="100" />
        <el-table-column label="数据">
          <template #default="{ row }">{{ JSON.stringify(row.data) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getDevice, getDeviceValues, getDeviceData, syncDevice, readDevice,
  writeDevice, invokeAction, putDeviceValues
} from '@/api/modules/devices'
import { getProduct } from '@/api/modules/products'

const route = useRoute()
const deviceId = route.params.deviceId
const loading = ref(false)
const ctrlLoading = ref(false)
const device = ref(null)
const product = ref(null)
const values = ref({})
const history = ref([])
const writeForm = reactive({})
const readPoints = ref([])
const simJson = ref('{"temperature": 36.5}')
const lastResponse = ref('')

const properties = computed(() => product.value?.model?.properties || [])
const actions = computed(() => product.value?.model?.actions || [])
const writableProps = computed(() =>
  properties.value.filter((p) => (p.mode || 'r').includes('w'))
)

const propLabel = (key) => properties.value.find((p) => p.name === key)?.label || key
const propUnit = (key) => properties.value.find((p) => p.name === key)?.unit || ''

const load = async () => {
  loading.value = true
  try {
    device.value = await getDevice(deviceId)
    const vals = await getDeviceValues(deviceId)
    values.value = vals.values || {}
    history.value = await getDeviceData(deviceId, { limit: 50 })
    try {
      product.value = await getProduct(device.value.product_id)
      writableProps.value.forEach((p) => {
        if (writeForm[p.name] === undefined) writeForm[p.name] = values.value[p.name] ?? ''
      })
    } catch {
      product.value = null
    }
  } finally {
    loading.value = false
  }
}

const refreshValues = async () => {
  const vals = await getDeviceValues(deviceId)
  values.value = vals.values || {}
}

const showResp = (data) => {
  lastResponse.value = JSON.stringify(data, null, 2)
}

const doSync = async () => {
  ctrlLoading.value = true
  try {
    showResp(await syncDevice(deviceId))
    ElMessage.success('同步完成')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '同步超时/失败')
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

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.resp {
  margin-top: 12px; background: #0f172a; color: #e2e8f0;
  padding: 12px; border-radius: 6px; font-size: 12px; max-height: 200px; overflow: auto;
}
</style>
