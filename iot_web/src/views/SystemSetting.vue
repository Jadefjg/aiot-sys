<template>
  <div class="setting-page">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card>
          <template #header>系统设置</template>
          <el-menu :default-active="module" @select="switchModule">
            <el-menu-item v-for="m in modules" :key="m.module" :index="m.module">
              {{ m.title }}
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      <el-col :span="18">
        <el-card v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>{{ moduleTitle }}</span>
              <el-button type="primary" :loading="saving" @click="save" v-if="authStore.isSuperuser">
                保存
              </el-button>
            </div>
          </template>
          <el-alert
            v-if="!authStore.isSuperuser"
            type="info"
            :closable="false"
            title="仅管理员可修改配置，当前为只读预览"
            style="margin-bottom: 16px"
          />
          <el-form label-width="160px" style="max-width: 640px">
            <el-form-item v-for="f in fields" :key="f.name" :label="f.label">
              <el-switch
                v-if="f.type === 'switch'"
                v-model="form[f.name]"
              />
              <el-select v-else-if="f.type === 'select'" v-model="form[f.name]" style="width: 100%">
                <el-option v-for="o in f.options" :key="o" :label="o" :value="o" />
              </el-select>
              <el-input
                v-else-if="f.type === 'password'"
                v-model="form[f.name]"
                type="password"
                show-password
              />
              <el-input-number
                v-else-if="f.type === 'number'"
                v-model="form[f.name]"
                style="width: 100%"
              />
              <el-input v-else v-model="form[f.name]" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/modules/auth'
import { getSettingModules, getSettingForm, getSettingValues, saveSettingValues } from '@/api/modules/settings'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const modules = ref([])
const fields = ref([])
const form = reactive({})
const module = ref(route.params.module || 'mqtt')

const moduleTitle = computed(() =>
  modules.value.find((m) => m.module === module.value)?.title || module.value
)

const loadModules = async () => {
  modules.value = await getSettingModules()
  if (!route.params.module && modules.value.length) {
    module.value = modules.value[0].module
  }
}

const loadForm = async () => {
  loading.value = true
  try {
    const [formDef, values] = await Promise.all([
      getSettingForm(module.value),
      getSettingValues(module.value),
    ])
    fields.value = formDef.fields || []
    Object.keys(form).forEach((k) => delete form[k])
    Object.assign(form, values.values || {})
  } catch {
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const switchModule = (m) => {
  module.value = m
  router.replace(`/settings/${m}`)
}

const save = async () => {
  saving.value = true
  try {
    await saveSettingValues(module.value, { ...form })
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

watch(() => route.params.module, (m) => {
  if (m) {
    module.value = m
    loadForm()
  }
})

onMounted(async () => {
  await loadModules()
  await loadForm()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
