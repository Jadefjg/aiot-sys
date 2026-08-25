<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>连接管理</span>
          <div>
            <span class="hint">MQTT：link/{linker}/{id}/open|close|up|down</span>
            <el-button v-if="canWrite" type="primary" @click="openCreate">新建连接</el-button>
          </div>
        </div>
      </template>
      <el-table :data="links" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="link_id" label="连接ID" width="140" />
        <el-table-column prop="linker" label="连接器" width="120" />
        <el-table-column prop="protocol" label="协议" width="100" />
        <el-table-column label="远端" width="180">
          <template #default="{ row }">{{ row.options?.host || '-' }}:{{ row.options?.port || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'open' ? 'success' : row.status === 'error' ? 'danger' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button v-if="canWrite" link type="primary" @click="doOpen(row)">打开</el-button>
            <el-button v-if="canWrite" link @click="doClose(row)">关闭</el-button>
            <el-button v-if="canWrite" link type="danger" @click="doDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" title="新建连接" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="连接ID"><el-input v-model="form.link_id" placeholder="link-1" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="连接器">
          <el-select v-model="form.linker" style="width: 100%">
            <el-option label="TCP 客户端" value="tcp-client" />
            <el-option label="串口 serial" value="serial" />
            <el-option label="UDP 客户端" value="udp-client" />
          </el-select>
        </el-form-item>
        <el-form-item label="协议">
          <el-select v-model="form.protocol" style="width: 100%">
            <el-option label="Modbus" value="modbus" />
            <el-option label="DL/T645" value="dlt645" />
            <el-option label="CJ/T188" value="cj188" />
            <el-option label="S7" value="s7" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机"><el-input v-model="form.host" placeholder="127.0.0.1" /></el-form-item>
        <el-form-item label="端口"><el-input-number v-model="form.port" :min="1" :max="65535" /></el-form-item>
        <el-form-item label="轮询(ms)"><el-input-number v-model="form.poll_interval" :min="200" :step="200" /></el-form-item>
        <el-form-item label="网关ID"><el-input v-model="form.gateway_id" placeholder="可选" /></el-form-item>
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
import { getLinks, createLink, deleteLink, openLink, closeLink } from '@/api/modules/links'

const authStore = useAuthStore()
const canWrite = computed(() => authStore.isSuperuser)

const loading = ref(false)
const links = ref([])
const visible = ref(false)
const form = reactive({
  link_id: '', name: '', linker: 'tcp-client', protocol: 'modbus',
  host: '127.0.0.1', port: 502, poll_interval: 1000, gateway_id: ''
})

const load = async () => {
  loading.value = true
  try {
    links.value = await getLinks()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  Object.assign(form, {
    link_id: `link-${Date.now().toString().slice(-6)}`,
    name: 'Modbus TCP', linker: 'tcp-client', protocol: 'modbus',
    host: '127.0.0.1', port: 502, poll_interval: 1000, gateway_id: ''
  })
  visible.value = true
}

const save = async () => {
  await createLink({
    link_id: form.link_id,
    name: form.name,
    linker: form.linker,
    protocol: form.protocol,
    gateway_id: form.gateway_id || null,
    options: { host: form.host, port: form.port, poll_interval: form.poll_interval }
  })
  ElMessage.success('连接已创建')
  visible.value = false
  load()
}

const doOpen = async (row) => {
  await openLink(row.link_id)
  ElMessage.success('已下发打开')
  setTimeout(load, 800)
}
const doClose = async (row) => {
  await closeLink(row.link_id)
  ElMessage.success('已关闭')
  load()
}
const doDelete = async (row) => {
  await ElMessageBox.confirm(`删除连接 ${row.name}?`)
  await deleteLink(row.link_id)
  load()
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.hint { font-size: 12px; color: #909399; margin-right: 12px; }
</style>
