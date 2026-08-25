<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>组织分组</span>
          <el-button type="primary" @click="openCreate">新建分组</el-button>
        </div>
      </template>
      <el-table :data="groups" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="parent_id" label="父分组" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="editing ? '编辑分组' : '新建分组'" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="父分组">
          <el-select v-model="form.parent_id" clearable placeholder="可选" style="width: 100%">
            <el-option
              v-for="g in groups.filter((x) => x.id !== editing?.id)"
              :key="g.id"
              :label="g.name"
              :value="g.id"
            />
          </el-select>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getGroups, createGroup, updateGroup, deleteGroup } from '@/api/modules/groups'

const loading = ref(false)
const groups = ref([])
const visible = ref(false)
const editing = ref(null)
const form = reactive({ name: '', description: '', parent_id: null })

const formatTime = (t) => (t ? new Date(t).toLocaleString('zh-CN') : '-')

const load = async () => {
  loading.value = true
  try {
    groups.value = await getGroups()
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = null
  Object.assign(form, { name: '', description: '', parent_id: null })
  visible.value = true
}

const openEdit = (row) => {
  editing.value = row
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    parent_id: row.parent_id
  })
  visible.value = true
}

const save = async () => {
  if (!form.name) {
    ElMessage.warning('请填写名称')
    return
  }
  const payload = {
    name: form.name,
    description: form.description || null,
    parent_id: form.parent_id || null
  }
  if (editing.value) await updateGroup(editing.value.id, payload)
  else await createGroup(payload)
  ElMessage.success('已保存')
  visible.value = false
  load()
}

const remove = async (row) => {
  await ElMessageBox.confirm(`删除分组 ${row.name}?`)
  await deleteGroup(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
