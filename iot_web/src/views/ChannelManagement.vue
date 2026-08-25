<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据通道</span>
          <div>
            <span class="hint">采集通道收数 · 资源通道落库/转发</span>
            <el-button v-if="canWrite" type="primary" @click="openCreate('collect')">新建采集</el-button>
            <el-button v-if="canWrite" @click="openCreate('resource')">新建资源</el-button>
          </div>
        </div>
      </template>
      <el-table :data="channels" v-loading="loading" stripe empty-text="暂无通道，请新建采集或资源通道">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="channel_id" label="通道ID" width="140" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.kind === 'collect' ? 'success' : 'warning'" size="small">
              {{ row.kind === 'collect' ? '采集' : '资源' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="protocol" label="协议" width="110" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="启用" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" :disabled="!canWrite" @change="(v) => toggle(row, v)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="showLogs(row)">日志</el-button>
            <el-button v-if="canWrite" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="form.kind === 'collect' ? '采集通道' : '资源通道'" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="通道ID"><el-input v-model="form.channel_id" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="协议">
          <el-select v-model="form.protocol" style="width: 100%">
            <el-option v-for="p in protocolOptions" :key="p" :label="p" :value="p" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.kind === 'collect' && form.protocol !== 'tcp' && !isIndustrial" label="连接ID">
          <el-input v-model="form.link_id" placeholder="Modbus/DLT645 绑定 link_id" />
        </el-form-item>
        <el-form-item v-if="form.kind === 'collect' && form.protocol === 'tcp'" label="监听端口">
          <el-input v-model="form.port" placeholder="9000" />
        </el-form-item>
        <el-form-item v-if="form.kind === 'collect' && (form.protocol === 'tcp' || isIndustrial)" label="默认设备">
          <el-input v-model="form.device_id" placeholder="写入的 device_id" />
        </el-form-item>
        <el-form-item v-if="isIndustrial" label="主机">
          <el-input v-model="form.host" placeholder="PLC / OPC UA 地址" />
        </el-form-item>
        <el-form-item v-if="isIndustrial" label="端口">
          <el-input v-model="form.port" :placeholder="industrialPortHint" />
        </el-form-item>
        <el-form-item v-if="isIndustrial" label="端点">
          <el-input v-model="form.endpoint" placeholder="opc.tcp://host:4840" />
        </el-form-item>
        <el-form-item v-if="isIndustrial" label="模拟">
          <el-switch v-model="form.simulate" />
          <span class="hint" style="margin-left: 8px">无实物时按测点生成数值</span>
        </el-form-item>
        <el-form-item v-if="isIndustrial" label="测点 JSON">
          <el-input v-model="form.pointsJson" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item v-if="form.kind === 'resource'" label="Webhook">
          <el-input v-model="form.url" placeholder="https://..." />
        </el-form-item>
        <el-form-item v-if="form.kind === 'resource'" label="MQTT主题">
          <el-input v-model="form.topic" placeholder="resource/{channel}/+/values" />
        </el-form-item>
        <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="logVisible" title="通道日志" size="420px">
      <el-timeline>
        <el-timeline-item v-for="log in logs" :key="log.id" :timestamp="formatTime(log.created_at)">
          {{ log.message }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logs.length" description="暂无日志" />
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import {
  getChannels, createChannel, deleteChannel, enableChannel, disableChannel, getChannelLogs
} from '@/api/modules/channels'

const authStore = useAuthStore()
const canWrite = computed(() => authStore.isSuperuser)

const loading = ref(false)
const channels = ref([])
const visible = ref(false)
const logVisible = ref(false)
const logs = ref([])
const form = reactive({
  channel_id: '', name: '', kind: 'collect', protocol: 'mqtt',
  link_id: '', port: '9000', device_id: '', host: '', endpoint: '',
  simulate: true, pointsJson: '[{"name":"temperature","node":"ns=2;s=Temp","ioa":1,"db":1,"offset":0}]',
  url: '', topic: '', description: ''
})

const protocolOptions = computed(() =>
  form.kind === 'collect'
    ? ['mqtt', 'modbus', 'dlt645', 'http', 'tcp', 'opcua', 's7', 'iec104', 'bacnet', 'knx']
    : ['influx', 'webhook', 'mqtt']
)
const isIndustrial = computed(() =>
  ['opcua', 's7', 'iec104', 'bacnet', 'knx'].includes(form.protocol)
)
const industrialPortHint = computed(() => ({
  opcua: '4840', s7: '102', iec104: '2404', bacnet: '47808', knx: '3671'
}[form.protocol] || '102'))

const load = async () => {
  loading.value = true
  try { channels.value = await getChannels() } finally { loading.value = false }
}

const openCreate = (kind) => {
  Object.assign(form, {
    channel_id: `ch-${Date.now().toString().slice(-6)}`,
    name: kind === 'collect' ? '采集通道' : '资源通道',
    kind, protocol: kind === 'collect' ? 'mqtt' : 'mysql',
    link_id: '', port: '9000', device_id: '', host: '', endpoint: '',
    simulate: true, pointsJson: '[{"name":"temperature","node":"ns=2;s=Temp","ioa":1,"db":1,"offset":0}]',
    url: '', topic: '', description: ''
  })
  visible.value = true
}

const save = async () => {
  const config = {}
  if (form.link_id) config.link_id = form.link_id
  if (form.protocol === 'tcp' && form.port) config.port = Number(form.port)
  if ((form.protocol === 'tcp' || isIndustrial.value) && form.device_id) config.device_id = form.device_id
  if (isIndustrial.value) {
    if (form.host) config.host = form.host
    if (form.port) config.port = Number(form.port)
    if (form.endpoint) config.endpoint = form.endpoint
    config.simulate = !!form.simulate
    try { config.points = JSON.parse(form.pointsJson || '[]') } catch { config.points = [] }
  }
  if (form.url) config.url = form.url
  if (form.topic) config.topic = form.topic
  await createChannel({
    channel_id: form.channel_id, name: form.name, kind: form.kind,
    protocol: form.protocol, config, description: form.description, enabled: false
  })
  ElMessage.success('通道已创建，请启用')
  visible.value = false
  load()
}

const toggle = async (row, enabled) => {
  try {
    if (enabled) await enableChannel(row.channel_id)
    else await disableChannel(row.channel_id)
  } catch {
    ElMessage.error('切换通道状态失败')
  } finally {
    load()
  }
}

const showLogs = async (row) => {
  logs.value = await getChannelLogs(row.channel_id)
  logVisible.value = true
}

const remove = async (row) => {
  await ElMessageBox.confirm(`删除通道 ${row.name}?`)
  await deleteChannel(row.channel_id)
  load()
}

const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN') : '-')
onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.hint { font-size: 12px; color: #909399; margin-right: 12px; }
</style>
