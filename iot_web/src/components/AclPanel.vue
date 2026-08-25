<template>
  <div>
    <p class="hint">viewer 只读 · operator 可控制 · admin 可删改并授权</p>
    <el-table :data="items" size="small" empty-text="暂无授权">
      <el-table-column prop="username" label="用户" />
      <el-table-column prop="role" label="角色" width="120" />
      <el-table-column v-if="canAdmin" label="操作" width="90">
        <template #default="{ row }">
          <el-button link type="danger" @click="$emit('revoke', row.user_id)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-form v-if="canAdmin" inline style="margin-top: 12px">
      <el-form-item label="用户">
        <el-select v-model="form.user_id" filterable placeholder="选择用户" style="width: 180px">
          <el-option v-for="u in users" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="form.role" style="width: 120px">
          <el-option label="viewer" value="viewer" />
          <el-option label="operator" value="operator" />
          <el-option label="admin" value="admin" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="grant">授权</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

defineProps({
  items: { type: Array, default: () => [] },
  users: { type: Array, default: () => [] },
  canAdmin: { type: Boolean, default: false }
})
const emit = defineEmits(['grant', 'revoke'])
const form = reactive({ user_id: null, role: 'viewer' })
const grant = () => {
  if (!form.user_id) return
  emit('grant', { user_id: form.user_id, role: form.role })
}
</script>

<style scoped>
.hint { font-size: 12px; color: #909399; margin: 0 0 8px; }
</style>
