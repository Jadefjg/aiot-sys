import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Auth/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'screen',
        name: 'DataScreen',
        component: () => import('@/views/DataScreen.vue'),
        meta: { title: '数据大屏' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/DevicesManagement.vue'),
        meta: { title: '设备管理' }
      },
      {
        path: 'devices/:deviceId',
        name: 'DeviceDetail',
        component: () => import('@/views/DeviceDetail.vue'),
        meta: { title: '设备详情' }
      },
      {
        path: 'protocols',
        name: 'Protocols',
        component: () => import('@/views/ProtocolManagement.vue'),
        meta: { title: '协议库' }
      },
      {
        path: 'links',
        name: 'Links',
        component: () => import('@/views/LinkManagement.vue'),
        meta: { title: '连接管理' }
      },
      {
        path: 'channels',
        name: 'Channels',
        component: () => import('@/views/ChannelManagement.vue'),
        meta: { title: '数据通道' }
      },
      {
        path: 'rules',
        name: 'Rules',
        component: () => import('@/views/RuleEngine.vue'),
        meta: { title: '规则引擎' }
      },
      {
        path: 'scada',
        name: 'Scada',
        component: () => import('@/views/ScadaView.vue'),
        meta: { title: '组态监控' }
      },
      {
        path: 'scada/design',
        name: 'ScadaDesign',
        component: () => import('@/views/ScadaDesigner.vue'),
        meta: { title: '组态设计' }
      },
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/ProductManagement.vue'),
        meta: { title: '产品物模型' }
      },
      {
        path: 'products/:productId',
        name: 'ProductDetail',
        component: () => import('@/views/ProductDetail.vue'),
        meta: { title: '产品详情' }
      },
      {
        path: 'alarms',
        name: 'Alarms',
        component: () => import('@/views/AlarmManagement.vue'),
        meta: { title: '告警中心' }
      },
      {
        path: 'scenes',
        name: 'Scenes',
        component: () => import('@/views/SceneManagement.vue'),
        meta: { title: '智能场景' }
      },
      {
        path: 'groups',
        name: 'Groups',
        component: () => import('@/views/GroupManagement.vue'),
        meta: { title: '组织分组' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/UserManagement.vue'),
        meta: { title: '用户管理', requiresSuperuser: true }
      },
      {
        path: 'firmware',
        name: 'Firmware',
        component: () => import('@/views/FirmwareUpgrade.vue'),
        meta: { title: '固件管理' }
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('@/views/RoleManagement.vue'),
        meta: { title: '角色管理', requiresSuperuser: true }
      },
      {
        path: 'settings/:module?',
        name: 'Settings',
        component: () => import('@/views/SystemSetting.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'password',
        name: 'Password',
        component: () => import('@/views/Auth/Password.vue'),
        meta: { title: '修改密码' }
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('@/views/PermissionManagement.vue'),
        meta: { title: '权限管理', requiresSuperuser: true }
      },
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory('/iot/'),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
    return
  }
  if (token && (to.path === '/login' || to.path === '/register')) {
    next('/dashboard')
    return
  }
  if (to.meta.requiresSuperuser) {
    const authStore = useAuthStore()
    if (authStore.token) {
      await authStore.fetchUser()
    }
    if (!authStore.isSuperuser) {
      next('/dashboard')
      return
    }
  }
  next()
})

export default router
