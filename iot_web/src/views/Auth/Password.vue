<template>
  <div class="password-page">
    <el-card style="max-width: 480px; margin: 40px auto">
      <template #header>修改密码</template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="新密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">保存</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { updateCurrentUser } from '@/api/modules/users'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ password: '', confirm: '' })

const rules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_, v, cb) => {
        if (v !== form.password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

const submit = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    await updateCurrentUser({ password: form.password })
    ElMessage.success('密码已更新')
    router.push('/dashboard')
  } catch {
    ElMessage.error('更新失败')
  } finally {
    loading.value = false
  }
}
</script>
