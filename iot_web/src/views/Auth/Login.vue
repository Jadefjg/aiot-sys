<template>
  <div class="login-container">
    <!-- 动态科技背景 -->
    <div class="tech-background">
      <!-- 神经网络连接线 -->
      <svg class="neural-network" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#00d4ff;stop-opacity:0" />
            <stop offset="50%" style="stop-color:#00d4ff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#00d4ff;stop-opacity:0" />
          </linearGradient>
          <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#00ff88;stop-opacity:0" />
            <stop offset="50%" style="stop-color:#00ff88;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#00ff88;stop-opacity:0" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <!-- 动态连接线 -->
        <g class="connections" filter="url(#glow)">
          <line v-for="(line, index) in connectionLines" :key="'line-'+index"
            :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
            :stroke="line.color" stroke-width="1" :opacity="line.opacity">
            <animate attributeName="opacity" :values="line.animValues" :dur="line.dur" repeatCount="indefinite"/>
          </line>
        </g>
        <!-- 神经节点 -->
        <g class="nodes">
          <g v-for="(node, index) in neuralNodes" :key="'node-'+index">
            <circle :cx="node.x" :cy="node.y" :r="node.r" :fill="node.color" filter="url(#glow)">
              <animate attributeName="r" :values="node.pulseValues" :dur="node.dur" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.5;1;0.5" :dur="node.dur" repeatCount="indefinite"/>
            </circle>
            <circle :cx="node.x" :cy="node.y" :r="node.r * 2" fill="none" :stroke="node.color" stroke-width="1" opacity="0.3">
              <animate attributeName="r" :values="`${node.r * 2};${node.r * 4};${node.r * 2}`" :dur="node.dur" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.3;0;0.3" :dur="node.dur" repeatCount="indefinite"/>
            </circle>
          </g>
        </g>
      </svg>

      <!-- 数据流粒子 -->
      <div class="data-streams">
        <div v-for="n in 30" :key="'stream-'+n" class="data-particle" :style="getParticleStyle(n)"></div>
      </div>

      <!-- 六边形网格 -->
      <div class="hex-grid">
        <div v-for="n in 20" :key="'hex-'+n" class="hexagon" :style="getHexStyle(n)"></div>
      </div>

      <!-- 扫描线效果 -->
      <div class="scan-line"></div>

      <!-- 浮动AI图标 -->
      <div class="floating-icons">
        <div v-for="n in 8" :key="'icon-'+n" class="ai-symbol" :style="getIconStyle(n)">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path v-if="n % 4 === 1" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            <path v-else-if="n % 4 === 2" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
            <path v-else-if="n % 4 === 3" d="M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"/>
            <path v-else d="M12 2l-5.5 9h11L12 2zm0 3.84L13.93 9h-3.87L12 5.84zM17.5 13c-2.49 0-4.5 2.01-4.5 4.5s2.01 4.5 4.5 4.5 4.5-2.01 4.5-4.5-2.01-4.5-4.5-4.5zm0 7c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
        </div>
      </div>

      <!-- 光晕效果 -->
      <div class="glow-effects">
        <div class="glow-orb glow-1"></div>
        <div class="glow-orb glow-2"></div>
        <div class="glow-orb glow-3"></div>
      </div>
    </div>

    <!-- 登录框 -->
    <div class="login-box">
      <div class="logo-section">
        <!-- AI大脑动态图标 -->
        <div class="ai-brain">
          <svg viewBox="0 0 120 120" class="brain-icon">
            <defs>
              <linearGradient id="brainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#00d4ff"/>
                <stop offset="100%" style="stop-color:#00ff88"/>
              </linearGradient>
            </defs>
            <!-- 中心核心 -->
            <circle cx="60" cy="60" r="15" fill="url(#brainGradient)" class="core">
              <animate attributeName="r" values="15;18;15" dur="2s" repeatCount="indefinite"/>
            </circle>
            <!-- 外环 -->
            <circle cx="60" cy="60" r="25" fill="none" stroke="url(#brainGradient)" stroke-width="2" stroke-dasharray="5,5" class="ring-1">
              <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="10s" repeatCount="indefinite"/>
            </circle>
            <circle cx="60" cy="60" r="35" fill="none" stroke="#00d4ff" stroke-width="1" stroke-dasharray="10,5" opacity="0.6" class="ring-2">
              <animateTransform attributeName="transform" type="rotate" from="360 60 60" to="0 60 60" dur="15s" repeatCount="indefinite"/>
            </circle>
            <!-- 连接节点 -->
            <g class="brain-nodes">
              <circle cx="60" cy="20" r="4" fill="#00d4ff"><animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/></circle>
              <circle cx="95" cy="40" r="4" fill="#00ff88"><animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite"/></circle>
              <circle cx="95" cy="80" r="4" fill="#00d4ff"><animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/></circle>
              <circle cx="60" cy="100" r="4" fill="#00ff88"><animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite"/></circle>
              <circle cx="25" cy="80" r="4" fill="#00d4ff"><animate attributeName="opacity" values="1;0.3;1" dur="1.8s" repeatCount="indefinite"/></circle>
              <circle cx="25" cy="40" r="4" fill="#00ff88"><animate attributeName="opacity" values="0.3;1;0.3" dur="1.8s" repeatCount="indefinite"/></circle>
            </g>
            <!-- 连接线 -->
            <g stroke="url(#brainGradient)" stroke-width="1" opacity="0.8">
              <line x1="60" y1="45" x2="60" y2="24"><animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.5s" repeatCount="indefinite"/></line>
              <line x1="72" y1="52" x2="91" y2="42"><animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.5s" repeatCount="indefinite"/></line>
              <line x1="72" y1="68" x2="91" y2="78"><animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite"/></line>
              <line x1="60" y1="75" x2="60" y2="96"><animate attributeName="opacity" values="0.2;0.8;0.2" dur="2s" repeatCount="indefinite"/></line>
              <line x1="48" y1="68" x2="29" y2="78"><animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.8s" repeatCount="indefinite"/></line>
              <line x1="48" y1="52" x2="29" y2="42"><animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" repeatCount="indefinite"/></line>
            </g>
          </svg>
        </div>
        <h2>AIoT 智能设备管理平台</h2>
        <p class="subtitle">
          <span class="typing-text">Artificial Intelligence of Things</span>
        </p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleLogin">
            <span class="btn-text">登 录</span>
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-link">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 生成神经网络节点
const neuralNodes = ref([])
const connectionLines = ref([])

onMounted(() => {
  generateNeuralNetwork()
})

const generateNeuralNetwork = () => {
  const nodes = []
  const lines = []
  const nodeCount = 25

  // 生成节点
  for (let i = 0; i < nodeCount; i++) {
    nodes.push({
      x: Math.random() * 1920,
      y: Math.random() * 1080,
      r: 3 + Math.random() * 4,
      color: Math.random() > 0.5 ? '#00d4ff' : '#00ff88',
      pulseValues: `${3 + Math.random() * 4};${5 + Math.random() * 4};${3 + Math.random() * 4}`,
      dur: `${2 + Math.random() * 3}s`
    })
  }

  // 生成连接线
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dist = Math.sqrt(Math.pow(nodes[i].x - nodes[j].x, 2) + Math.pow(nodes[i].y - nodes[j].y, 2))
      if (dist < 300) {
        lines.push({
          x1: nodes[i].x,
          y1: nodes[i].y,
          x2: nodes[j].x,
          y2: nodes[j].y,
          color: Math.random() > 0.5 ? 'url(#lineGradient)' : 'url(#lineGradient2)',
          opacity: 0.3 + Math.random() * 0.4,
          animValues: `${0.1 + Math.random() * 0.3};${0.5 + Math.random() * 0.5};${0.1 + Math.random() * 0.3}`,
          dur: `${2 + Math.random() * 4}s`
        })
      }
    }
  }

  neuralNodes.value = nodes
  connectionLines.value = lines
}

// 粒子样式
const getParticleStyle = (n) => {
  const delay = Math.random() * 5
  const duration = 3 + Math.random() * 4
  const left = Math.random() * 100
  const size = 2 + Math.random() * 3
  return {
    left: `${left}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

// 六边形样式
const getHexStyle = (n) => {
  const left = Math.random() * 100
  const top = Math.random() * 100
  const size = 30 + Math.random() * 50
  const delay = Math.random() * 5
  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${size}px`,
    height: `${size}px`,
    animationDelay: `${delay}s`
  }
}

// 浮动图标样式
const getIconStyle = (n) => {
  const left = 5 + Math.random() * 90
  const top = 5 + Math.random() * 90
  const delay = Math.random() * 3
  const duration = 4 + Math.random() * 4
  return {
    left: `${left}%`,
    top: `${top}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  }
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await authStore.login(form.username, form.password)
        if (success) {
          ElMessage.success('登录成功')
          router.push('/dashboard')
        } else {
          ElMessage.error('用户名或密码错误')
        }
      } catch (error) {
        ElMessage.error('登录失败，请稍后重试')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 30%, #0f1629 70%, #0a0a1a 100%);
  position: relative;
  overflow: hidden;
}

/* 科技背景层 */
.tech-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* 神经网络SVG */
.neural-network {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0.8;
}

/* 数据流粒子 */
.data-streams {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.data-particle {
  position: absolute;
  bottom: -10px;
  background: linear-gradient(to top, #00d4ff, transparent);
  border-radius: 50%;
  animation: dataRise linear infinite;
  box-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff;
}

@keyframes dataRise {
  0% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translateY(-110vh) scale(0.5);
    opacity: 0;
  }
}

/* 六边形网格 */
.hex-grid {
  position: absolute;
  width: 100%;
  height: 100%;
}

.hexagon {
  position: absolute;
  border: 1px solid rgba(0, 212, 255, 0.2);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  animation: hexPulse 4s ease-in-out infinite;
}

@keyframes hexPulse {
  0%, 100% {
    opacity: 0.1;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(1.1);
  }
}

/* 扫描线 */
.scan-line {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, #00ff88, #00d4ff, transparent);
  animation: scanMove 4s linear infinite;
  box-shadow: 0 0 20px #00d4ff, 0 0 40px #00d4ff;
}

@keyframes scanMove {
  0% {
    top: -2px;
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}

/* 浮动AI图标 */
.floating-icons {
  position: absolute;
  width: 100%;
  height: 100%;
}

.ai-symbol {
  position: absolute;
  width: 30px;
  height: 30px;
  color: rgba(0, 212, 255, 0.3);
  animation: floatIcon 6s ease-in-out infinite;
}

@keyframes floatIcon {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.2;
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
    opacity: 0.5;
  }
}

/* 光晕效果 */
.glow-effects {
  position: absolute;
  width: 100%;
  height: 100%;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  animation: orbPulse 6s ease-in-out infinite;
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
  animation-delay: 2s;
}

.glow-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(138, 43, 226, 0.25) 0%, transparent 70%);
  top: 50%;
  left: 30%;
  animation-delay: 4s;
}

@keyframes orbPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.9;
  }
}

/* 登录框 */
.login-box {
  width: 420px;
  padding: 40px;
  background: rgba(15, 20, 40, 0.85);
  border-radius: 20px;
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 1px rgba(0, 212, 255, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  backdrop-filter: blur(20px);
  position: relative;
  z-index: 10;
  animation: boxAppear 0.8s ease-out;
}

.login-box::before {
  content: '';
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.3), transparent, rgba(0, 255, 136, 0.3));
  z-index: -1;
  animation: borderGlow 3s ease-in-out infinite;
}

@keyframes borderGlow {
  0%, 100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}

@keyframes boxAppear {
  0% {
    opacity: 0;
    transform: translateY(40px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Logo区域 */
.logo-section {
  text-align: center;
  margin-bottom: 30px;
}

.ai-brain {
  width: 100px;
  height: 100px;
  margin: 0 auto 20px;
}

.brain-icon {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 15px rgba(0, 212, 255, 0.6));
}

.login-box h2 {
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-bottom: 10px;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

.subtitle {
  color: #00d4ff;
  font-size: 12px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

.typing-text {
  display: inline-block;
  overflow: hidden;
  border-right: 2px solid #00d4ff;
  white-space: nowrap;
  animation: typing 3s steps(30) infinite, blink 0.5s step-end infinite alternate;
}

@keyframes typing {
  0%, 90%, 100% {
    width: 100%;
  }
}

@keyframes blink {
  50% {
    border-color: transparent;
  }
}

/* 表单样式 */
:deep(.el-input__wrapper) {
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 10px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #00d4ff;
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

:deep(.el-input__prefix) {
  color: #00d4ff;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #00d4ff 0%, #00a0cc 50%, #0080aa 100%);
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 4px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

:deep(.el-button--primary::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: btnShine 2s infinite;
}

@keyframes btnShine {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #00e5ff 0%, #00b8e6 50%, #0099cc 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 40px rgba(0, 212, 255, 0.5);
}

.register-link {
  text-align: center;
  margin-top: 25px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.register-link a {
  color: #00d4ff;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.register-link a:hover {
  color: #00ff88;
  text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
}
</style>
