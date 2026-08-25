<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon><Monitor /></el-icon>
        <span>IoT管理系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item-group title="控制台">
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/screen">
            <el-icon><DataBoard /></el-icon>
            <span>数据大屏</span>
          </el-menu-item>
        </el-menu-item-group>

        <el-menu-item-group title="物联网">
          <el-menu-item index="/products">
            <el-icon><Box /></el-icon>
            <span>产品物模型</span>
          </el-menu-item>
          <el-menu-item index="/protocols">
            <el-icon><Connection /></el-icon>
            <span>协议库</span>
          </el-menu-item>
          <el-menu-item index="/links">
            <el-icon><Link /></el-icon>
            <span>连接管理</span>
          </el-menu-item>
          <el-menu-item index="/channels">
            <el-icon><Share /></el-icon>
            <span>数据通道</span>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Cpu /></el-icon>
            <span>设备管理</span>
          </el-menu-item>
          <el-menu-item index="/alarms">
            <el-icon><Bell /></el-icon>
            <span>告警中心</span>
          </el-menu-item>
          <el-menu-item index="/scenes">
            <el-icon><SetUp /></el-icon>
            <span>智能场景</span>
          </el-menu-item>
          <el-menu-item index="/rules">
            <el-icon><Filter /></el-icon>
            <span>规则引擎</span>
          </el-menu-item>
          <el-menu-item index="/scada">
            <el-icon><Grid /></el-icon>
            <span>组态监控</span>
          </el-menu-item>
          <el-menu-item index="/scada/design">
            <el-icon><EditPen /></el-icon>
            <span>组态设计</span>
          </el-menu-item>
          <el-menu-item index="/groups">
            <el-icon><OfficeBuilding /></el-icon>
            <span>组织分组</span>
          </el-menu-item>
          <el-menu-item index="/firmware">
            <el-icon><Upload /></el-icon>
            <span>固件管理</span>
          </el-menu-item>
        </el-menu-item-group>

        <el-menu-item-group title="用户与权限">
          <el-menu-item index="/settings/mqtt">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item v-if="authStore.isSuperuser" index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item v-if="authStore.isSuperuser" index="/roles">
            <el-icon><UserFilled /></el-icon>
            <span>角色管理</span>
          </el-menu-item>
          <el-menu-item v-if="authStore.isSuperuser" index="/permissions">
            <el-icon><Key /></el-icon>
            <span>权限管理</span>
          </el-menu-item>
        </el-menu-item-group>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><Avatar /></el-icon>
              {{ authStore.username || '用户' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main" :class="{ 'no-pad': $route.path === '/screen' }">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/settings')) return '/settings/mqtt'
  if (path.startsWith('/scada/design')) return '/scada/design'
  const parents = [
    '/products', '/devices', '/protocols', '/links', '/channels',
    '/alarms', '/scenes', '/rules', '/scada', '/groups', '/firmware',
    '/users', '/roles', '/permissions'
  ]
  const hit = parents.find((p) => path === p || path.startsWith(`${p}/`))
  return hit || path
})

onMounted(() => {
  if (authStore.token) authStore.fetchUser()
})

const handleCommand = (command) => {
  if (command === 'password') {
    router.push('/password')
  } else if (command === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside { background-color: #001529; overflow-y: auto; }
.logo {
  height: 60px; display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 18px; font-weight: bold; gap: 8px;
}
.logo .el-icon { font-size: 24px; }
.header {
  background-color: #fff; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex; align-items: center; justify-content: flex-end; padding: 0 20px;
}
.user-info { display: flex; align-items: center; gap: 5px; cursor: pointer; }
.main { background-color: #f0f2f5; padding: 20px; }
.main.no-pad { padding: 0; background: #0b1220; }
:deep(.el-menu-item-group__title) {
  color: rgba(255,255,255,0.45) !important;
  font-size: 12px;
  padding-left: 20px !important;
}
</style>
