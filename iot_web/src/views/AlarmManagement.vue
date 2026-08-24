<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警中心</span>
          <el-radio-group v-model="ackFilter" size="small" @change="fetchAlarms">
            <el-radio-button :label="null">全部</el-radio-button>
            <el-radio-button :label="false">未确认</el-radio-button>
            <el-radio-button :label="true">已确认</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="alarms" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="90">
          <template #default="{ row }">
            <el-tag :type="levelType(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="message" label="消息" show-overflow-tooltip />
        <el-table-column prop="product_id" label="产品" width="120" />
        <el-table-column prop="validator_name" label="规则" width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            {{ row.acknowledged ? '已确认' : '未确认' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="!row.acknowledged"
              link
              type="primary"
              @click="ack(row)"
            >确认</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAlarms, acknowledgeAlarm } from '@/api/modules/alarms'

const loading = ref(false)
const alarms = ref([])
const ackFilter = ref(false)

const levelType = (level) => ({
  info: 'info', warning: 'warning', error: 'danger', critical: 'danger'
}[level] || 'info')

const fetchAlarms = async () => {
  loading.value = true
  try {
    const params = {}
    if (ackFilter.value !== null) params.acknowledged = ackFilter.value
    alarms.value = await getAlarms(params)
  } finally {
    loading.value = false
  }
}

const ack = async (row) => {
  await acknowledgeAlarm(row.id)
  ElMessage.success('已确认')
  fetchAlarms()
}

onMounted(fetchAlarms)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
