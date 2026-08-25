<template>
  <div class="designer" v-loading="loading">
    <div class="bar">
      <span>组态设计</span>
      <el-select v-model="productId" filterable placeholder="选择产品" style="width: 240px" @change="load">
        <el-option v-for="p in products" :key="p.product_id" :label="p.name" :value="p.product_id" />
      </el-select>
      <el-button type="primary" size="small" :disabled="!productId" @click="save">保存画布</el-button>
      <el-button size="small" @click="$router.push('/scada')">返回监控</el-button>
    </div>
    <div class="workspace">
      <div class="palette">
        <div class="panel-title">控件</div>
        <div v-for="t in types" :key="t.type" class="pal-item" draggable="true" @dragstart="onDragType(t.type)">
          {{ t.label }}
        </div>
      </div>
      <div class="canvas-wrap" @dragover.prevent @drop="onDrop">
        <div class="canvas" :style="{ width: layout.width + 'px', height: layout.height + 'px' }">
          <div
            v-for="w in layout.widgets"
            :key="w.id"
            class="widget"
            :class="{ active: selectedId === w.id }"
            :style="widgetStyle(w)"
            @mousedown.stop="startMove($event, w)"
          >
            <div class="w-title">{{ w.label || w.prop || w.type }}</div>
            <div class="w-body">{{ previewText(w) }}</div>
            <span class="resize" @mousedown.stop="startResize($event, w)" />
          </div>
        </div>
      </div>
      <div class="inspector">
        <div class="panel-title">属性</div>
        <el-empty v-if="!selected" description="点选画布中的控件" :image-size="48" />
        <el-form v-else label-width="72px" size="small">
          <el-form-item label="类型">{{ selected.type }}</el-form-item>
          <el-form-item label="标题"><el-input v-model="selected.label" /></el-form-item>
          <el-form-item label="属性">
            <el-select v-model="selected.prop" filterable allow-create style="width: 100%">
              <el-option v-for="p in properties" :key="p.name" :label="p.label || p.name" :value="p.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="最小"><el-input-number v-model="selected.min" :step="1" /></el-form-item>
          <el-form-item label="最大"><el-input-number v-model="selected.max" :step="1" /></el-form-item>
          <el-form-item>
            <el-button type="danger" plain @click="removeSelected">删除控件</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProduct, getProducts, updateProductConfig } from '@/api/modules/products'

const types = [
  { type: 'value', label: '数值' },
  { type: 'gauge', label: '仪表' },
  { type: 'switch', label: '开关' },
  { type: 'lamp', label: '指示灯' },
  { type: 'label', label: '文本' },
  { type: 'button', label: '按钮' },
]
const loading = ref(false)
const products = ref([])
const productId = ref('')
const product = ref(null)
const dragType = ref('')
const selectedId = ref('')
const route = useRoute()
const layout = reactive({ width: 960, height: 560, widgets: [] })
let moving = null

const properties = computed(() => product.value?.model?.properties || [])
const selected = computed(() => layout.widgets.find((w) => w.id === selectedId.value) || null)

const widgetStyle = (w) => ({
  left: w.x + 'px', top: w.y + 'px', width: w.w + 'px', height: w.h + 'px'
})
const previewText = (w) => (w.type === 'switch' ? 'OFF' : w.type === 'lamp' ? '●' : w.prop || '--')

const onDragType = (type) => { dragType.value = type }
const onDrop = (ev) => {
  const rect = ev.currentTarget.querySelector('.canvas').getBoundingClientRect()
  addWidget(dragType.value || 'value', ev.clientX - rect.left, ev.clientY - rect.top)
}

const addWidget = (type, x, y) => {
  const id = `w${Date.now().toString(36)}`
  layout.widgets.push({
    id, type, x: Math.max(0, x - 40), y: Math.max(0, y - 20),
    w: type === 'gauge' ? 180 : 140, h: type === 'gauge' ? 140 : 88,
    prop: properties.value[0]?.name || '', label: types.find((t) => t.type === type)?.label || type,
    min: 0, max: 100
  })
  selectedId.value = id
}

const startMove = (ev, w) => {
  selectedId.value = w.id
  moving = { mode: 'move', w, x: ev.clientX, y: ev.clientY, ox: w.x, oy: w.y }
}
const startResize = (ev, w) => {
  selectedId.value = w.id
  moving = { mode: 'resize', w, x: ev.clientX, y: ev.clientY, ow: w.w, oh: w.h }
}
const onMouseMove = (ev) => {
  if (!moving) return
  const dx = ev.clientX - moving.x
  const dy = ev.clientY - moving.y
  if (moving.mode === 'move') {
    moving.w.x = Math.max(0, moving.ox + dx)
    moving.w.y = Math.max(0, moving.oy + dy)
  } else {
    moving.w.w = Math.max(80, moving.ow + dx)
    moving.w.h = Math.max(56, moving.oh + dy)
  }
}
const onMouseUp = () => { moving = null }
const removeSelected = () => {
  layout.widgets = layout.widgets.filter((w) => w.id !== selectedId.value)
  selectedId.value = ''
}

const applyLayout = (cfg) => {
  layout.width = cfg?.width || 960
  layout.height = cfg?.height || 560
  layout.widgets = Array.isArray(cfg?.widgets) ? cfg.widgets.map((w) => ({ ...w })) : []
}

const load = async () => {
  if (!productId.value) return
  loading.value = true
  try {
    product.value = await getProduct(productId.value)
    applyLayout(product.value?.config?.scada)
  } finally {
    loading.value = false
  }
}

const save = async () => {
  if (!productId.value) return
  await updateProductConfig(productId.value, 'scada', {
    width: layout.width, height: layout.height, widgets: layout.widgets
  })
  ElMessage.success('组态已保存到产品配置')
}

onMounted(async () => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  products.value = await getProducts().catch(() => [])
  const q = route.query.productId
  productId.value = (Array.isArray(q) ? q[0] : q) || products.value[0]?.product_id || ''
  if (productId.value) await load()
})
onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})
</script>

<style scoped>
.designer { min-height: 70vh; }
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; font-weight: 600; }
.workspace { display: grid; grid-template-columns: 140px 1fr 220px; gap: 12px; min-height: 580px; }
.palette, .inspector {
  background: #fff; border: 1px solid #ebeef5; border-radius: 8px; padding: 10px;
}
.panel-title { font-weight: 600; color: #606266; margin-bottom: 8px; }
.pal-item {
  padding: 8px; margin-bottom: 6px; background: #f5f7fa; border-radius: 6px;
  cursor: grab; text-align: center; font-size: 13px;
}
.canvas-wrap { overflow: auto; background: #eef2f6; border-radius: 8px; padding: 12px; }
.canvas {
  position: relative; background: #0f172a;
  background-image: linear-gradient(#1e293b 1px, transparent 1px), linear-gradient(90deg, #1e293b 1px, transparent 1px);
  background-size: 20px 20px; border-radius: 6px;
}
.widget {
  position: absolute; background: linear-gradient(180deg, #1d4ed8 0%, #0f172a 100%);
  color: #fff; border-radius: 8px; padding: 8px; box-sizing: border-box; cursor: move;
  border: 1px solid transparent;
}
.widget.active { border-color: #67e8f9; }
.w-title { font-size: 12px; opacity: 0.85; }
.w-body { font-size: 20px; font-weight: 700; margin-top: 6px; }
.resize {
  position: absolute; right: 4px; bottom: 4px; width: 10px; height: 10px;
  background: #67e8f9; cursor: nwse-resize; border-radius: 2px;
}
</style>
