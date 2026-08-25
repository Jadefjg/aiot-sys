<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>规则引擎</span>
          <el-button v-if="canWrite" type="primary" @click="openCreate">新建规则</el-button>
        </div>
      </template>
      <el-table :data="rules" v-loading="loading" stripe empty-text="暂无规则">
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="product_id" label="产品" width="140" />
        <el-table-column label="条件" show-overflow-tooltip>
          <template #default="{ row }">{{ row.field }} {{ row.operator }} {{ row.value }}</template>
        </el-table-column>
        <el-table-column label="动作" width="140">
          <template #default="{ row }">{{ (row.actions || []).map(a => a.type).join(',') || 'alarm' }}</template>
        </el-table-column>
        <el-table-column label="启用" width="80">
          <template #default="{ row }">
            <el-switch :model-value="row.enabled" :disabled="!canWrite" @change="(v) => toggle(row, v)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button v-if="canWrite" link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" title="新建规则" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="产品ID"><el-input v-model="form.product_id" placeholder="可空=全部" /></el-form-item>
        <el-form-item label="字段"><el-input v-model="form.field" placeholder="temperature" /></el-form-item>
        <el-form-item label="条件">
          <el-select v-model="form.operator" style="width: 90px">
            <el-option v-for="op in ['>','>=','<','<=','==','!=']" :key="op" :label="op" :value="op" />
          </el-select>
          <el-input v-model="form.value" style="width: 160px; margin-left: 8px" />
        </el-form-item>
        <el-form-item label="动作">
          <el-select v-model="form.actionType" style="width: 100%">
            <el-option label="告警" value="alarm" />
            <el-option label="MQTT 转发" value="mqtt" />
            <el-option label="Webhook" value="webhook" />
            <el-option label="写设备" value="write" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.actionType === 'webhook'" label="URL">
          <el-input v-model="form.url" />
        </el-form-item>
        <el-form-item v-if="form.actionType === 'mqtt'" label="主题">
          <el-input v-model="form.topic" />
        </el-form-item>
        <el-form-item v-if="form.actionType === 'write'" label="目标设备">
          <el-input v-model="form.write_device" placeholder="可空=触发设备" />
        </el-form-item>
        <el-form-item v-if="form.actionType === 'write'" label="写入JSON">
          <el-input v-model="form.write_values" type="textarea" :rows="2" placeholder='{"switch": true}' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import { getRules, createRule, updateRule, deleteRule } from '@/api/modules/channels'

const authStore = useAuthStore()
const canWrite = computed(() => authStore.hasPermission('rule:write'))

const loading = ref(false)
const rules = ref([])
const visible = ref(false)
const form = reactive({
  name: '', product_id: '', field: 'temperature', operator: '>', value: '30',
  actionType: 'alarm', url: '', topic: '', write_device: '', write_values: '{"switch": true}'
})

const load = async () => {
  loading.value = true
  try {
    rules.value = await getRules()
  } catch {
    rules.value = []
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, {
    name: '', product_id: '', field: 'temperature', operator: '>', value: '30',
    actionType: 'alarm', url: '', topic: '', write_device: '', write_values: '{"switch": true}'
  })
  visible.value = true
}

const parseJson = (text, fallback = {}) => {
  try { return JSON.parse(text || '{}') } catch { return fallback }
}

const save = async () => {
  if (!form.name?.trim() || !form.field?.trim()) {
    ElMessage.warning('请填写规则名称与字段')
    return
  }
  const num = Number(form.value)
  const action = { type: form.actionType }
  if (form.url) action.url = form.url
  if (form.topic) action.topic = form.topic
  if (form.actionType === 'write') {
    action.device_id = form.write_device || null
    action.values = parseJson(form.write_values, {})
    if (!Object.keys(action.values).length) {
      ElMessage.warning('写设备动作需要填写写入JSON')
      return
    }
  }
  try {
    await createRule({
      name: form.name,
      product_id: form.product_id || null,
      field: form.field,
      operator: form.operator,
      value: Number.isNaN(num) ? form.value : num,
      enabled: true,
      actions: [action]
    })
    ElMessage.success('规则已创建')
    visible.value = false
    load()
  } catch {
    /* 全局拦截器已提示 */
  }
}

const toggle = async (row, enabled) => { await updateRule(row.id, { enabled }); load() }
const remove = async (row) => {
  await ElMessageBox.confirm(`删除规则 ${row.name}?`)
  await deleteRule(row.id)
  load()
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
