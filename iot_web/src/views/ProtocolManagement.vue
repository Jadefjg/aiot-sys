<template>
  <div class="protocol-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>协议库</span>
          <span class="hint">内置工业/物联网协议元数据，供产品接入参考</span>
        </div>
      </template>

      <el-table :data="protocols" v-loading="loading" stripe @row-click="showDetail">
        <el-table-column prop="title" label="协议名称" width="180" />
        <el-table-column prop="name" label="标识" width="120" />
        <el-table-column prop="transport" label="传输层" width="120" />
        <el-table-column label="实现" width="90">
          <template #default="{ row }">
            <el-tag :type="row.implemented ? 'success' : 'info'" size="small">
              {{ row.implemented ? '已接入' : '元数据' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="运行时" width="90">
          <template #default="{ row }">
            <el-tag :type="row.runtime ? 'success' : 'info'" size="small">
              {{ row.runtime ? '已注册' : '目录' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="description" label="说明" show-overflow-tooltip />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" :title="detail?.title || '协议详情'" size="480px">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="标识">{{ detail.name }}</el-descriptions-item>
        <el-descriptions-item label="传输">{{ detail.transport }}</el-descriptions-item>
        <el-descriptions-item label="默认端口">{{ detail.default_port || '-' }}</el-descriptions-item>
        <el-descriptions-item label="说明">{{ detail.description }}</el-descriptions-item>
      </el-descriptions>
      <h4 v-if="detail?.fields?.length" style="margin: 16px 0 8px">配置字段</h4>
      <el-table v-if="detail?.fields?.length" :data="detail.fields" size="small">
        <el-table-column prop="label" label="字段" />
        <el-table-column prop="name" label="键" width="120" />
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column prop="default" label="默认" width="80" />
      </el-table>
      <el-collapse v-if="detail?.topics?.length" style="margin-top: 16px">
        <el-collapse-item title="MQTT 主题模板">
          <el-tag v-for="t in detail.topics" :key="t" style="margin: 4px">{{ t }}</el-tag>
        </el-collapse-item>
      </el-collapse>
      <pre v-if="detail" class="json-block">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getProtocols, getProtocol } from '@/api/modules/protocols'

const loading = ref(false)
const protocols = ref([])
const drawerVisible = ref(false)
const detail = ref(null)

const load = async () => {
  loading.value = true
  try {
    protocols.value = await getProtocols()
  } catch {
    ElMessage.error('加载协议库失败')
  } finally {
    loading.value = false
  }
}

const showDetail = async (row) => {
  try {
    detail.value = await getProtocol(row.name)
    drawerVisible.value = true
  } catch {
    ElMessage.error('加载协议详情失败')
  }
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; align-items: center; gap: 12px; }
.hint { font-size: 13px; color: #909399; font-weight: normal; }
.json-block {
  margin-top: 16px; background: #0f172a; color: #e2e8f0;
  padding: 12px; border-radius: 6px; font-size: 12px; max-height: 240px; overflow: auto;
}
</style>
