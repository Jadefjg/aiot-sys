<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能场景 / 定时 / 联动</span>
          <div>
            <el-tag v-if="gatewayFilter" type="info" style="margin-right: 8px">网关: {{ gatewayFilter }}</el-tag>
            <el-button type="primary" @click="openScene">新建场景</el-button>
            <el-button @click="openJob">新建定时</el-button>
            <el-button @click="openBinding">新建联动</el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="tab">
        <el-tab-pane label="场景" name="scenes">
          <el-table :data="scenes" v-loading="loading" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="gateway_id" label="网关" width="140" />
            <el-table-column label="启用" width="80">
              <template #default="{ row }">
                <el-switch :model-value="row.enabled" @change="(v) => toggleScene(row, v)" />
              </template>
            </el-table-column>
            <el-table-column label="触发/动作" show-overflow-tooltip>
              <template #default="{ row }">
                {{ (row.triggers || []).length }} 触发 / {{ (row.actions || []).length }} 动作
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="danger" @click="removeScene(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="定时任务" name="jobs">
          <el-table :data="jobs" v-loading="loading" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="cron_time" label="时间" width="120" />
            <el-table-column prop="gateway_id" label="网关" width="140" />
            <el-table-column label="启用" width="80">
              <template #default="{ row }">
                <el-switch :model-value="row.enabled" @change="(v) => toggleJob(row, v)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="danger" @click="removeJob(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="设备联动" name="bindings">
          <el-table :data="bindings" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="device1_id" label="设备 A" />
            <el-table-column prop="device2_id" label="设备 B" />
            <el-table-column label="双向" width="80">
              <template #default="{ row }">{{ row.bidirectional ? '是' : '否' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link type="danger" @click="removeBinding(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="脚本" name="scripts">
          <el-table :data="scripts" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="language" label="语言" width="80" />
            <el-table-column prop="interval_seconds" label="间隔(秒)" width="110" />
            <el-table-column prop="gateway_id" label="网关" width="140" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button link type="primary" @click="openScript(row)">查看</el-button>
                <el-button link type="danger" @click="removeScript(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button style="margin-top: 8px" @click="openScript()">新建脚本</el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="sceneVisible" title="新建场景" width="560px">
      <el-form :model="sceneForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="sceneForm.name" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="sceneForm.gateway_id" /></el-form-item>
        <el-form-item label="触发设备"><el-input v-model="sceneForm.trigger_device" placeholder="device_id" /></el-form-item>
        <el-form-item label="触发属性"><el-input v-model="sceneForm.trigger_prop" placeholder="temperature" /></el-form-item>
        <el-form-item label="条件">
          <el-select v-model="sceneForm.trigger_op" style="width: 90px">
            <el-option v-for="op in ['>','>=','<','<=','==','!=']" :key="op" :label="op" :value="op" />
          </el-select>
          <el-input v-model="sceneForm.trigger_value" style="width: 140px; margin-left: 8px" placeholder="阈值" />
        </el-form-item>
        <el-form-item label="动作设备"><el-input v-model="sceneForm.action_device" /></el-form-item>
        <el-form-item label="写入JSON">
          <el-input v-model="sceneForm.action_values" type="textarea" :rows="2" placeholder='{"switch": true}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sceneVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScene">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="jobVisible" title="新建定时任务" width="480px">
      <el-form :model="jobForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="jobForm.name" /></el-form-item>
        <el-form-item label="时间"><el-input v-model="jobForm.cron_time" placeholder="08:00" /></el-form-item>
        <el-form-item label="目标设备"><el-input v-model="jobForm.device_id" /></el-form-item>
        <el-form-item label="写入JSON"><el-input v-model="jobForm.data_json" type="textarea" :rows="2" placeholder='{"switch": true}' /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="jobForm.gateway_id" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="jobVisible = false">取消</el-button>
        <el-button type="primary" @click="saveJob">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="bindingVisible" title="新建联动" width="460px">
      <el-form :model="bindingForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="bindingForm.name" /></el-form-item>
        <el-form-item label="设备 A"><el-input v-model="bindingForm.device1_id" /></el-form-item>
        <el-form-item label="设备 B"><el-input v-model="bindingForm.device2_id" /></el-form-item>
        <el-form-item label="双向"><el-switch v-model="bindingForm.bidirectional" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="bindingForm.gateway_id" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindingVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBinding">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="scriptVisible" title="边缘脚本" width="640px">
      <el-form :model="scriptForm" label-width="90px">
        <el-form-item label="名称"><el-input v-model="scriptForm.name" /></el-form-item>
        <el-form-item label="语言">
          <el-select v-model="scriptForm.language" style="width: 160px">
            <el-option label="JavaScript" value="js" />
            <el-option label="Lua" value="lua" />
          </el-select>
        </el-form-item>
        <el-form-item label="间隔秒"><el-input-number v-model="scriptForm.interval_seconds" :min="0" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="scriptForm.gateway_id" /></el-form-item>
        <el-form-item label="内容">
          <el-input v-model="scriptForm.content" type="textarea" :rows="10" :placeholder="scriptPlaceholder" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scriptVisible = false">取消</el-button>
        <el-button @click="preview">试运行</el-button>
        <el-button type="primary" @click="saveScript">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import {
  getScenes, createScene, updateScene, deleteScene,
  getJobs, createJob, updateJob, deleteJob,
  getBindings, createBinding, deleteBinding,
  getScripts, createScript, updateScript, deleteScript, previewScript
} from '@/api/modules/scenes'

const route = useRoute()
const authStore = useAuthStore()
const gatewayFilter = ref(route.query.gateway_id || '')
const tab = ref('scenes')
const loading = ref(false)
const scenes = ref([])
const jobs = ref([])
const bindings = ref([])
const scripts = ref([])
const sceneVisible = ref(false)
const jobVisible = ref(false)
const bindingVisible = ref(false)
const scriptVisible = ref(false)
const sceneForm = reactive({
  name: '', gateway_id: '', trigger_device: '', trigger_prop: 'temperature',
  trigger_op: '>', trigger_value: '30', action_device: '', action_values: '{"switch": true}'
})
const jobForm = reactive({ name: '', cron_time: '08:00', gateway_id: '', device_id: '', data_json: '{}' })
const bindingForm = reactive({ name: '', device1_id: '', device2_id: '', bidirectional: true, gateway_id: '' })
const scriptForm = reactive({ name: '', content: '', language: 'js', interval_seconds: 0, gateway_id: '' })
const scriptPlaceholder = computed(() =>
  scriptForm.language === 'lua'
    ? 'if values.temperature > 30 then write(device_id, {fan=1}) end'
    : 'if (values.temperature > 30) { write(device_id, {fan: 1}); }'
)

const gwParams = () => (gatewayFilter.value ? { gateway_id: gatewayFilter.value } : {})

const load = async () => {
  loading.value = true
  const params = gwParams()
  try {
    const [sceneRes, jobRes, bindingRes, scriptRes] = await Promise.allSettled([
      getScenes(params),
      getJobs(params),
      getBindings(params),
      getScripts(params)
    ])
    scenes.value = sceneRes.status === 'fulfilled' ? sceneRes.value : []
    jobs.value = jobRes.status === 'fulfilled' ? jobRes.value : []
    bindings.value = bindingRes.status === 'fulfilled' ? bindingRes.value : []
    scripts.value = scriptRes.status === 'fulfilled' ? scriptRes.value : []
  } finally {
    loading.value = false
  }
}

const parseJson = (text, fallback = {}) => {
  try { return JSON.parse(text || '{}') } catch { return fallback }
}

const openScene = () => {
  Object.assign(sceneForm, {
    name: '', gateway_id: gatewayFilter.value || '', trigger_device: '', trigger_prop: 'temperature',
    trigger_op: '>', trigger_value: '30', action_device: '', action_values: '{"switch": true}'
  })
  sceneVisible.value = true
}
const openJob = () => {
  Object.assign(jobForm, { name: '', cron_time: '08:00', gateway_id: gatewayFilter.value || '', device_id: '', data_json: '{}' })
  jobVisible.value = true
}
const openBinding = () => {
  Object.assign(bindingForm, { name: '', device1_id: '', device2_id: '', bidirectional: true, gateway_id: gatewayFilter.value || '' })
  bindingVisible.value = true
}
const openScript = (row) => {
  Object.assign(scriptForm, row
    ? { ...row, language: row.language || 'js' }
    : { name: '', content: '', language: 'js', interval_seconds: 0, gateway_id: gatewayFilter.value || '' })
  scriptVisible.value = true
}

const saveScene = async () => {
  const value = Number(sceneForm.trigger_value)
  await createScene({
    name: sceneForm.name,
    gateway_id: sceneForm.gateway_id || null,
    enabled: true,
    triggers: [{
      device_id: sceneForm.trigger_device,
      property: sceneForm.trigger_prop,
      operator: sceneForm.trigger_op,
      value: Number.isNaN(value) ? sceneForm.trigger_value : value
    }],
    actions: [{
      type: 'write',
      device_id: sceneForm.action_device,
      values: parseJson(sceneForm.action_values)
    }]
  })
  ElMessage.success('场景已创建，属性上报时云端执行')
  sceneVisible.value = false
  load()
}

const saveJob = async () => {
  if (!jobForm.name?.trim() || !jobForm.device_id?.trim()) {
    ElMessage.warning('请填写任务名称与目标设备')
    return
  }
  if (!authStore.isSuperuser && !jobForm.gateway_id) {
    ElMessage.warning('非管理员请填写网关ID')
    return
  }
  try {
    await createJob({
      name: jobForm.name,
      cron_time: jobForm.cron_time,
      gateway_id: jobForm.gateway_id || null,
      enabled: true,
      action: { type: 'write', device_id: jobForm.device_id },
      data: parseJson(jobForm.data_json)
    })
    ElMessage.success('任务已创建')
    jobVisible.value = false
    load()
  } catch { /* 全局提示 */ }
}

const saveBinding = async () => {
  if (!bindingForm.device1_id || !bindingForm.device2_id) {
    ElMessage.warning('请填写设备 A / B')
    return
  }
  try {
    await createBinding({ ...bindingForm, gateway_id: bindingForm.gateway_id || null })
    ElMessage.success('联动已创建')
    bindingVisible.value = false
    load()
  } catch { /* 全局提示 */ }
}

const preview = async () => {
  const res = await previewScript({
    content: scriptForm.content,
    language: scriptForm.language,
    device_id: scriptForm.gateway_id || 'demo-meter-1',
    values: { temperature: 35 }
  })
  ElMessage.success(`试运行：写入 ${JSON.stringify(res.writes || [])}`)
}

const saveScript = async () => {
  if (!scriptForm.name?.trim() || !scriptForm.content?.trim()) {
    ElMessage.warning('请填写脚本名称与内容')
    return
  }
  if (!authStore.isSuperuser && !scriptForm.gateway_id) {
    ElMessage.warning('非管理员请填写网关ID')
    return
  }
  try {
    const payload = { ...scriptForm, gateway_id: scriptForm.gateway_id || null }
    if (scriptForm.id) await updateScript(scriptForm.id, payload)
    else await createScript(payload)
    ElMessage.success('脚本已保存，属性上报或按间隔在云端执行')
    scriptVisible.value = false
    load()
  } catch { /* 全局提示 */ }
}

const toggleScene = async (row, enabled) => { await updateScene(row.id, { enabled }); load() }
const toggleJob = async (row, enabled) => { await updateJob(row.id, { enabled }); load() }
const removeScene = async (row) => { await ElMessageBox.confirm(`删除场景 ${row.name}?`); await deleteScene(row.id); load() }
const removeJob = async (row) => { await ElMessageBox.confirm(`删除任务 ${row.name}?`); await deleteJob(row.id); load() }
const removeBinding = async (row) => { await ElMessageBox.confirm('删除该联动?'); await deleteBinding(row.id); load() }
const removeScript = async (row) => { await ElMessageBox.confirm(`删除脚本 ${row.name}?`); await deleteScript(row.id); load() }

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
