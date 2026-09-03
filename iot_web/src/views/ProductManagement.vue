<template>
  <div class="products-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>产品与物模型</span>
          <el-button type="primary" @click="openCreate">添加产品</el-button>
        </div>
      </template>

      <el-table :data="products" v-loading="loading" stripe>
        <el-table-column prop="product_id" label="产品ID" width="160" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="protocol" label="协议" width="100" />
        <el-table-column prop="version" label="版本" width="90" />
        <el-table-column label="能力" width="220">
          <template #default="{ row }">
            <el-tag v-if="row.is_gateway" size="small">网关</el-tag>
            <el-tag v-if="row.ota" size="small" type="success">OTA</el-tag>
            <el-tag v-if="row.controllable" size="small" type="info">可控</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="物模型" width="120">
          <template #default="{ row }">
            {{ (row.model?.properties || []).length }} 属性 /
            {{ (row.model?.validators || []).length }} 规则
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openModel(row)" v-if="canProductAdmin(row.product_id)">物模型</el-button>
            <el-button link type="primary" @click="openEdit(row)" v-if="canProductAdmin(row.product_id)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)" v-if="canProductAdmin(row.product_id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="formVisible" :title="editing ? '编辑产品' : '添加产品'" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="产品ID" required>
          <el-input v-model="form.product_id" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="协议">
          <el-select
            v-model="form.protocol"
            filterable
            placeholder="从协议库选择"
            style="width: 100%"
          >
            <el-option
              v-for="item in protocolOptions"
              :key="item.name"
              :label="`${item.title || item.name} (${item.name})`"
              :value="item.name"
            >
              <span>{{ item.title || item.name }}</span>
              <span class="protocol-opt-meta">{{ item.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="能力">
          <el-checkbox v-model="form.is_gateway">网关</el-checkbox>
          <el-checkbox v-model="form.ota">OTA</el-checkbox>
          <el-checkbox v-model="form.controllable">可控</el-checkbox>
          <el-checkbox v-model="form.writable">可写</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProduct">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="modelVisible" title="编辑物模型" width="1080px" top="5vh">
      <el-tabs v-model="modelTab">
        <el-tab-pane label="属性" name="properties">
          <el-button size="small" @click="addProp" style="margin-bottom: 8px">添加属性</el-button>
          <el-table :data="modelDraft.properties" size="small">
            <el-table-column label="标识">
              <template #default="{ row }"><el-input v-model="row.name" size="small" /></template>
            </el-table-column>
            <el-table-column label="名称">
              <template #default="{ row }"><el-input v-model="row.label" size="small" /></template>
            </el-table-column>
            <el-table-column label="类型" width="110">
              <template #default="{ row }">
                <el-select v-model="row.type" size="small">
                  <el-option value="number" /><el-option value="string" />
                  <el-option value="boolean" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="模式" width="90">
              <template #default="{ row }">
                <el-select v-model="row.mode" size="small">
                  <el-option value="r" /><el-option value="w" /><el-option value="rw" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="单位" width="70">
              <template #default="{ row }"><el-input v-model="row.unit" size="small" /></template>
            </el-table-column>
            <el-table-column label="地址" width="90">
              <template #default="{ row }"><el-input v-model="row.address" size="small" placeholder="寄存器" /></template>
            </el-table-column>
            <el-table-column label="公式" width="110">
              <template #default="{ row }"><el-input v-model="row.formula" size="small" placeholder="%s*0.1" /></template>
            </el-table-column>
            <el-table-column label="" width="50">
              <template #default="{ $index }">
                <el-button link type="danger" @click="modelDraft.properties.splice($index, 1)">删</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="动作" name="actions">
          <el-button size="small" @click="modelDraft.actions.push({ name: '', label: '', type: 'button' })">添加</el-button>
          <el-table :data="modelDraft.actions" size="small" style="margin-top: 8px">
            <el-table-column label="标识">
              <template #default="{ row }"><el-input v-model="row.name" size="small" /></template>
            </el-table-column>
            <el-table-column label="名称">
              <template #default="{ row }"><el-input v-model="row.label" size="small" /></template>
            </el-table-column>
            <el-table-column label="" width="60">
              <template #default="{ $index }">
                <el-button link type="danger" @click="modelDraft.actions.splice($index, 1)">删</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="告警规则" name="validators">
          <el-button size="small" @click="addValidator">添加规则</el-button>
          <el-table :data="modelDraft.validators" size="small" style="margin-top: 8px">
            <el-table-column label="字段" width="120">
              <template #default="{ row }"><el-input v-model="row.field" size="small" /></template>
            </el-table-column>
            <el-table-column label="运算符" width="90">
              <template #default="{ row }">
                <el-select v-model="row.operator" size="small">
                  <el-option v-for="op in ['>', '>=', '<', '<=', '==', '!=']" :key="op" :value="op" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="阈值" width="100">
              <template #default="{ row }"><el-input v-model="row.value" size="small" /></template>
            </el-table-column>
            <el-table-column label="标题">
              <template #default="{ row }"><el-input v-model="row.title" size="small" /></template>
            </el-table-column>
            <el-table-column label="消息">
              <template #default="{ row }"><el-input v-model="row.message" size="small" placeholder="{field}" /></template>
            </el-table-column>
            <el-table-column label="" width="60">
              <template #default="{ $index }">
                <el-button link type="danger" @click="modelDraft.validators.splice($index, 1)">删</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="modelVisible = false">取消</el-button>
        <el-button type="primary" @click="saveModel">保存物模型</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="产品详情" width="760px" top="5vh">
      <div v-loading="detailLoading">
        <template v-if="detailProduct">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="产品ID">{{ detailProduct.product_id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ detailProduct.name }}</el-descriptions-item>
            <el-descriptions-item label="协议">{{ detailProduct.protocol || '-' }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ detailProduct.version || '-' }}</el-descriptions-item>
            <el-descriptions-item label="能力">
              <el-tag v-if="detailProduct.is_gateway" size="small">网关</el-tag>
              <el-tag v-if="detailProduct.ota" size="small" type="success">OTA</el-tag>
              <el-tag v-if="detailProduct.controllable" size="small" type="info">可控</el-tag>
              <el-tag v-if="detailProduct.writable" size="small" type="warning">可写</el-tag>
              <span v-if="!detailProduct.is_gateway && !detailProduct.ota && !detailProduct.controllable && !detailProduct.writable">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="物模型">
              {{ (detailProduct.model?.properties || []).length }} 属性 /
              {{ (detailProduct.model?.actions || []).length }} 动作 /
              {{ (detailProduct.model?.validators || []).length }} 规则
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ detailProduct.description || '-' }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">物模型属性</el-divider>
          <el-table
            :data="detailProduct.model?.properties || []"
            size="small"
            empty-text="暂无属性"
            max-height="200"
          >
            <el-table-column prop="name" label="标识" />
            <el-table-column prop="label" label="名称" />
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column prop="mode" label="模式" width="70" />
            <el-table-column prop="unit" label="单位" width="70" />
            <el-table-column prop="address" label="地址" width="80" />
            <el-table-column prop="formula" label="公式" />
          </el-table>

          <el-divider content-position="left">协议配置</el-divider>
          <el-text v-if="!configKeys.length" type="info">暂无协议配置</el-text>
          <el-tag v-for="key in configKeys" :key="key" style="margin-right: 8px">{{ key }}</el-tag>
        </template>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" @click="goFullDetail">完整详情页</el-button>
        <el-button type="success" @click="openModelFromDetail">编辑物模型</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import {
  getProducts, getProduct, createProduct, updateProduct, updateThingModel, deleteProduct
} from '@/api/modules/products'
import { getProtocols } from '@/api/modules/protocols'
import { unwrapList } from '@/utils/apiHelpers'

const authStore = useAuthStore()
const canProductAdmin = (pid) => authStore.isSuperuser || authStore.productRole(pid) === 'admin'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const products = ref([])
const formVisible = ref(false)
const modelVisible = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailProduct = ref(null)
const editing = ref(null)
const currentProduct = ref(null)
const modelTab = ref('properties')
const form = reactive({
  product_id: '', name: '', protocol: 'mqtt', version: '1.0',
  description: '', is_gateway: false, ota: false, controllable: true, writable: true
})
const modelDraft = reactive({
  properties: [], events: [], actions: [], validators: [], settings: []
})
const protocols = ref([])

const protocolOptions = computed(() => {
  const list = unwrapList(protocols.value)
  const names = new Set(list.map((item) => item.name))
  if (form.protocol && !names.has(form.protocol)) {
    return [{ name: form.protocol, title: form.protocol }, ...list]
  }
  return list
})

const loadProtocols = async () => {
  try {
    protocols.value = unwrapList(await getProtocols())
  } catch {
    protocols.value = []
    ElMessage.error('加载协议库失败')
  }
}

const configKeys = computed(() => {
  const config = detailProduct.value?.config
  return config && typeof config === 'object' ? Object.keys(config) : []
})

const fetchProducts = async () => {
  loading.value = true
  try {
    const list = await getProducts()
    products.value = Array.isArray(list) ? list : []
    const editId = route.query.edit
    if (editId) {
      const row = products.value.find((p) => p.product_id === editId)
      if (row) openModel(row)
    }
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    product_id: '', name: '', protocol: 'mqtt', version: '1.0',
    description: '', is_gateway: false, ota: false, controllable: true, writable: true
  })
}

const openCreate = () => {
  editing.value = null
  resetForm()
  loadProtocols()
  formVisible.value = true
}
const openEdit = (row) => {
  editing.value = row
  Object.assign(form, {
    product_id: row.product_id, name: row.name, protocol: row.protocol,
    version: row.version, description: row.description,
    is_gateway: row.is_gateway, ota: row.ota,
    controllable: row.controllable, writable: row.writable
  })
  loadProtocols()
  formVisible.value = true
}

const openDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  detailProduct.value = null
  try {
    detailProduct.value = await getProduct(row.product_id)
  } catch (error) {
    console.error('加载产品详情失败:', error)
    ElMessage.error('加载产品详情失败')
    detailVisible.value = false
  } finally {
    detailLoading.value = false
  }
}

const goFullDetail = () => {
  if (!detailProduct.value) return
  detailVisible.value = false
  router.push({ name: 'ProductDetail', params: { productId: detailProduct.value.product_id } })
}

const openModelFromDetail = () => {
  if (!detailProduct.value) return
  detailVisible.value = false
  openModel(detailProduct.value)
}

const saveProduct = async () => {
  if (!form.product_id || !form.name) {
    ElMessage.warning('请填写产品ID和名称')
    return
  }
  if (editing.value) {
    await updateProduct(form.product_id, { ...form })
  } else {
    await createProduct({ ...form, model: { properties: [], events: [], actions: [], validators: [], settings: [] } })
  }
  ElMessage.success('已保存')
  formVisible.value = false
  fetchProducts()
}

const openModel = (row) => {
  currentProduct.value = row
  const m = row.model || {}
  modelDraft.properties = JSON.parse(JSON.stringify(m.properties || []))
  modelDraft.events = JSON.parse(JSON.stringify(m.events || []))
  modelDraft.actions = JSON.parse(JSON.stringify(m.actions || []))
  modelDraft.validators = JSON.parse(JSON.stringify(m.validators || []))
  modelDraft.settings = JSON.parse(JSON.stringify(m.settings || []))
  modelVisible.value = true
}

const addProp = () => modelDraft.properties.push({
  name: '', label: '', type: 'number', mode: 'r', unit: '', address: '', formula: ''
})
const addValidator = () => modelDraft.validators.push({
  type: 'compare', field: '', operator: '>', value: 0, title: '告警', message: '{field} 超限', level: 'warning'
})

const saveModel = async () => {
  // 阈值转数字
  modelDraft.validators.forEach((v) => {
    if (v.value !== '' && !Number.isNaN(Number(v.value))) v.value = Number(v.value)
  })
  await updateThingModel(currentProduct.value.product_id, { ...modelDraft })
  ElMessage.success('物模型已同步')
  modelVisible.value = false
  fetchProducts()
}

const remove = async (row) => {
  await ElMessageBox.confirm(`删除产品 ${row.name}?`, '确认')
  await deleteProduct(row.product_id)
  ElMessage.success('已删除')
  fetchProducts()
}

onMounted(() => {
  fetchProducts()
  loadProtocols()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.protocol-opt-meta { float: right; color: #909399; font-size: 12px; margin-left: 12px; }
</style>
