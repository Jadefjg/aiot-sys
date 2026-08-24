<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能场景 / 定时任务</span>
          <div>
            <el-button type="primary" @click="openScene">新建场景</el-button>
            <el-button @click="openJob">新建定时</el-button>
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
      </el-tabs>
    </el-card>

    <el-dialog v-model="sceneVisible" title="新建场景" width="480px">
      <el-form :model="sceneForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="sceneForm.name" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="sceneForm.gateway_id" /></el-form-item>
        <el-form-item label="说明">
          <el-text type="info">触发器与动作可在创建JSON 中扩展；边缘网关负责执行。</el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sceneVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScene">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="jobVisible" title="新建定时任务" width="480px">
      <el-form :model="jobForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="jobForm.name" /></el-form-item>
        <el-form-item label="时间"><el-input v-model="jobForm.cron_time" placeholder="08:00" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="jobForm.gateway_id" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="jobVisible = false">取消</el-button>
        <el-button type="primary" @click="saveJob">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getScenes, createScene, updateScene, deleteScene,
  getJobs, createJob, updateJob, deleteJob
} from '@/api/modules/scenes'

const tab = ref('scenes')
const loading = ref(false)
const scenes = ref([])
const jobs = ref([])
const sceneVisible = ref(false)
const jobVisible = ref(false)
const sceneForm = reactive({ name: '', gateway_id: '', triggers: [], actions: [], enabled: true })
const jobForm = reactive({ name: '', cron_time: '08:00', gateway_id: '', enabled: true })

const load = async () => {
  loading.value = true
  try {
    scenes.value = await getScenes()
    jobs.value = await getJobs()
  } finally {
    loading.value = false
  }
}

const openScene = () => {
  Object.assign(sceneForm, { name: '', gateway_id: '', triggers: [], actions: [], enabled: true })
  sceneVisible.value = true
}
const openJob = () => {
  Object.assign(jobForm, { name: '', cron_time: '08:00', gateway_id: '', enabled: true })
  jobVisible.value = true
}

const saveScene = async () => {
  await createScene({ ...sceneForm })
  ElMessage.success('场景已创建')
  sceneVisible.value = false
  load()
}
const saveJob = async () => {
  await createJob({ ...jobForm })
  ElMessage.success('任务已创建')
  jobVisible.value = false
  load()
}

const toggleScene = async (row, enabled) => {
  await updateScene(row.id, { enabled })
  load()
}
const toggleJob = async (row, enabled) => {
  await updateJob(row.id, { enabled })
  load()
}

const removeScene = async (row) => {
  await ElMessageBox.confirm(`删除场景 ${row.name}?`)
  await deleteScene(row.id)
  load()
}
const removeJob = async (row) => {
  await ElMessageBox.confirm(`删除任务 ${row.name}?`)
  await deleteJob(row.id)
  load()
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
