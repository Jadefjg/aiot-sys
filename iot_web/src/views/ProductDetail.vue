<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/products')" :content="`产品 ${productId}`" />

    <el-card style="margin-top: 16px" v-if="product">
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="产品ID">{{ product.product_id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ product.name }}</el-descriptions-item>
        <el-descriptions-item label="协议">{{ product.protocol || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ product.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="能力">
          <el-tag v-if="product.is_gateway" size="small">网关</el-tag>
          <el-tag v-if="product.ota" size="small" type="success">OTA</el-tag>
          <el-tag v-if="product.controllable" size="small" type="info">可控</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="物模型">
          {{ (product.model?.properties || []).length }} 属性 /
          {{ (product.model?.actions || []).length }} 动作 /
          {{ (product.model?.validators || []).length }} 规则
        </el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 12px">
          <el-button v-if="canAdmin" type="primary" @click="$router.push({ path: '/products', query: { edit: productId } })">编辑物模型</el-button>
      </div>
    </el-card>

    <el-card style="margin-top: 16px" v-if="product">
      <template #header>
        <div class="card-header">
          <span>协议配置 product/{id}/config/{name}</span>
          <el-button v-if="canAdmin" type="primary" size="small" @click="saveConfig">保存并同步 MQTT</el-button>
        </div>
      </template>
      <el-form label-width="100px" style="max-width: 640px">
        <el-form-item label="配置名">
          <el-input v-model="configName" placeholder="modbus / dlt645 / s7" />
        </el-form-item>
        <el-form-item label="JSON">
          <el-input v-model="configJson" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <el-text type="info">Modbus 示例：slave_id + points[{name,address,quantity,type,scale,function}]</el-text>
    </el-card>

    <el-card style="margin-top: 16px" v-if="product">
      <template #header>
        <div class="card-header">
          <span>物解析</span>
          <el-button v-if="canAdmin" type="primary" size="small" @click="saveParser">保存解析规则</el-button>
        </div>
      </template>
      <el-form label-width="100px" style="max-width: 640px">
        <el-form-item label="类型">
          <el-select v-model="parser.type" style="width: 240px">
            <el-option label="JSON / 透传" value="json" />
            <el-option label="字段映射" value="map" />
            <el-option label="十六进制帧" value="hex" />
            <el-option label="键值串" value="kv" />
          </el-select>
        </el-form-item>
        <el-form-item label="映射 JSON">
          <el-input v-model="parser.mappingJson" type="textarea" :rows="8" />
        </el-form-item>
      </el-form>
      <el-text type="info">
        map 示例：{"temp":"temperature"}；hex 示例：{"temperature":{"offset":0,"len":2,"scale":0.1,"endian":"be"}}
      </el-text>
    </el-card>

    <el-card style="margin-top: 16px" v-if="product">
      <template #header>
        <div class="card-header">
          <span>物接入 / 物存储</span>
          <el-button v-if="canAdmin" type="primary" size="small" @click="saveChannels">绑定通道</el-button>
        </div>
      </template>
      <el-form label-width="100px" style="max-width: 640px">
        <el-form-item label="节点类型">
          <el-select v-model="dgiot.node_type" style="width: 240px">
            <el-option label="直连设备" value="direct" />
            <el-option label="网关设备" value="gateway" />
            <el-option label="网关子设备" value="subdevice" />
          </el-select>
        </el-form-item>
        <el-form-item label="联网方式">
          <el-select v-model="dgiot.network" style="width: 240px">
            <el-option label="MQTT" value="mqtt" />
            <el-option label="以太网" value="ethernet" />
            <el-option label="Wi-Fi" value="wifi" />
            <el-option label="NB-IoT" value="nbiot" />
          </el-select>
        </el-form-item>
        <el-form-item label="采集通道">
          <el-select v-model="dgiot.ingest_channels" multiple filterable style="width: 100%">
            <el-option v-for="c in collectChannels" :key="c.channel_id" :label="c.name" :value="c.channel_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="存储通道">
          <el-select v-model="dgiot.storage_channels" multiple filterable style="width: 100%">
            <el-option v-for="c in resourceChannels" :key="c.channel_id" :label="c.name" :value="c.channel_id" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 16px" v-if="product && canAdmin">
      <template #header>
        <div class="card-header">
          <span>产品授权</span>
        </div>
      </template>
      <AclPanel
        :items="aclItems"
        :users="aclUsers"
        :can-admin="canAdmin"
        @grant="onGrantAcl"
        @revoke="onRevokeAcl"
      />
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        <div class="card-header">
          <span>产品下设备</span>
          <el-button type="primary" size="small" @click="$router.push({ path: '/devices', query: { product_id: productId } })">
            去创建设备
          </el-button>
        </div>
      </template>
      <el-table :data="devices" stripe>
        <el-table-column prop="device_id" label="设备ID" />
        <el-table-column prop="device_name" label="名称" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="gateway_id" label="网关" width="140" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/devices/${row.device_id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProduct, updateProductConfig, bindProductChannels } from '@/api/modules/products'
import { getDevices } from '@/api/modules/devices'
import { getChannels } from '@/api/modules/channels'
import { useAuthStore } from '@/store/modules/auth'
import AclPanel from '@/components/AclPanel.vue'
import { getProductAcl, grantProductAcl, revokeProductAcl, getAclUsers } from '@/api/modules/acl'

const authStore = useAuthStore()
const aclItems = ref([])
const aclUsers = ref([])
const myRole = ref(null)
const canAdmin = computed(() => authStore.isSuperuser || myRole.value === 'admin')

const route = useRoute()
const productId = route.params.productId
const loading = ref(false)
const product = ref(null)
const devices = ref([])
const configName = ref('modbus')
const configJson = ref(JSON.stringify({
  slave_id: 1,
  points: [
    { name: 'temperature', address: 0, quantity: 1, type: 'int16', scale: 0.1, function: 3 }
  ]
}, null, 2))
const parser = reactive({
  type: 'json',
  mappingJson: '{\n  "temp": "temperature"\n}'
})
const dgiot = reactive({
  node_type: 'direct', network: 'mqtt', ingest_channels: [], storage_channels: []
})
const collectChannels = ref([])
const resourceChannels = ref([])

const saveChannels = async () => {
  product.value = await bindProductChannels(productId, { ...dgiot })
  ElMessage.success('已绑定物接入/物存储通道')
}

const onGrantAcl = async (body) => {
  await grantProductAcl(productId, body)
  ElMessage.success('已授权')
  const acl = await getProductAcl(productId)
  myRole.value = acl.my_role
  aclItems.value = acl.items || []
}
const onRevokeAcl = async (userId) => {
  await revokeProductAcl(productId, userId)
  const acl = await getProductAcl(productId)
  aclItems.value = acl.items || []
}

const saveParser = async () => {
  try {
    const mapping = JSON.parse(parser.mappingJson || '{}')
    product.value = await updateProductConfig(productId, 'parser', {
      type: parser.type,
      mapping
    })
    ElMessage.success('物解析已保存')
  } catch (e) {
    ElMessage.error(e.message || '映射 JSON 无效')
  }
}

const saveConfig = async () => {
  try {
    const parsed = JSON.parse(configJson.value)
    product.value = await updateProductConfig(productId, configName.value, parsed)
    ElMessage.success(`已发布 product/${productId}/config/${configName.value}`)
  } catch (e) {
    ElMessage.error(e.message || 'JSON 无效')
  }
}

const applyDgiot = (cfg) => {
  const d = cfg?.dgiot || {}
  dgiot.node_type = d.node_type || 'direct'
  dgiot.network = d.network || 'mqtt'
  dgiot.ingest_channels = [...(d.ingest_channels || [])]
  dgiot.storage_channels = [...(d.storage_channels || [])]
}

onMounted(async () => {
  loading.value = true
  try {
    product.value = await getProduct(productId)
    if (product.value?.config) {
      const cfg = product.value.config
      applyDgiot(cfg)
      if (cfg.parser) {
        parser.type = cfg.parser.type || 'json'
        parser.mappingJson = JSON.stringify(cfg.parser.mapping || {}, null, 2)
      }
      const keys = Object.keys(cfg).filter((k) => k !== 'dgiot' && k !== 'parser')
      if (keys.length) {
        configName.value = keys[0]
        configJson.value = JSON.stringify(cfg[keys[0]], null, 2)
      }
    }
    const [list, chCollect, chResource] = await Promise.all([
      getDevices({ product_id: productId }),
      getChannels({ kind: 'collect' }),
      getChannels({ kind: 'resource' })
    ])
    devices.value = Array.isArray(list) ? list : (list?.devices || [])
    collectChannels.value = Array.isArray(chCollect) ? chCollect : []
    resourceChannels.value = Array.isArray(chResource) ? chResource : []
    try {
      const acl = await getProductAcl(productId)
      myRole.value = acl.my_role
      aclItems.value = acl.items || []
      if (canAdmin.value) aclUsers.value = await getAclUsers().catch(() => [])
    } catch {
      myRole.value = authStore.productRole(productId)
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
