<template>
  <div class="register-container">
    <div class="glow-orb glow-1"></div>
    <div class="glow-orb glow-2"></div>
    <div class="register-box">
      <h2>注册账号</h2>
      <p class="subtitle">Artificial Intelligence of Things</p>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="邮箱"
            prefix-icon="Message"
            size="large"
            autocomplete="email"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            native-type="button"
            size="large"
            :loading="loading"
            style="width: 100%"
            @click.prevent="handleRegister"
          >
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-link">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/modules/auth'
import { ElMessage } from 'element-plus'
import { formatApiDetail } from '@/utils/apiHelpers'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value || loading.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await register({
      username: form.username,
      email: form.email,
      password: form.password
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(formatApiDetail(error.response?.data?.detail) || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 30%, #0f1629 70%, #0a0a1a 100%);
  position: relative;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
}

.glow-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.4) 0%, transparent 70%);
  top: -100px;
  left: -100px;
}

.glow-2 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(0, 255, 136, 0.3) 0%, transparent 70%);
  bottom: -50px;
  right: -50px;
}

.register-box {
  width: 420px;
  padding: 40px;
  background: rgba(15, 20, 40, 0.85);
  border-radius: 20px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5), 0 0 1px rgba(0, 212, 255, 0.5);
  border: 1px solid rgba(0, 212, 255, 0.2);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 10;
}

.register-box h2 {
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-bottom: 8px;
  text-align: center;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.subtitle {
  color: #00d4ff;
  font-size: 12px;
  letter-spacing: 3px;
  text-transform: uppercase;
  text-align: center;
  margin-bottom: 28px;
}

:deep(.el-form-item) {
  --el-input-bg-color: #0b1a2e;
  --el-input-text-color: #e8f4ff;
  --el-input-placeholder-color: rgba(180, 220, 255, 0.45);
  --el-input-border-color: rgba(0, 212, 255, 0.28);
  --el-input-hover-border-color: rgba(0, 212, 255, 0.55);
  --el-input-focus-border-color: #00d4ff;
  --el-fill-color-blank: #0b1a2e;
}

:deep(.el-input__wrapper) {
  background-color: #0b1a2e !important;
  background-image: none !important;
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.28) inset !important;
  border-radius: 10px;
}

:deep(.el-form-item.is-error .el-input__wrapper) {
  background-color: #0b1a2e !important;
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.7) inset !important;
}

:deep(.el-input__inner) {
  color: #e8f4ff !important;
  background-color: transparent !important;
  -webkit-text-fill-color: #e8f4ff;
  caret-color: #00d4ff;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(180, 220, 255, 0.45);
  -webkit-text-fill-color: rgba(180, 220, 255, 0.45);
}

:deep(.el-input__prefix),
:deep(.el-input__suffix),
:deep(.el-input__prefix-inner),
:deep(.el-input__suffix-inner) {
  color: #00d4ff;
}

:deep(input.el-input__inner:-webkit-autofill),
:deep(input.el-input__inner:-webkit-autofill:hover),
:deep(input.el-input__inner:-webkit-autofill:focus),
:deep(.el-input__wrapper:has(input:-webkit-autofill)) {
  -webkit-text-fill-color: #e8f4ff !important;
  caret-color: #00d4ff;
  transition: background-color 99999s ease-out 0s;
  box-shadow: 0 0 0 1000px #0b1a2e inset !important;
  background-color: #0b1a2e !important;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #00d4ff 0%, #00a0cc 50%, #0080aa 100%);
  border: none;
  border-radius: 10px;
  font-weight: 600;
  letter-spacing: 4px;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #00e5ff 0%, #00b8e6 50%, #0099cc 100%);
  box-shadow: 0 10px 40px rgba(0, 212, 255, 0.5);
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.login-link a {
  color: #00d4ff;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  color: #00ff88;
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
}
</style>
