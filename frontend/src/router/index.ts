import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { hasPerm } from '@/utils/permission'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'meetings',
        name: 'meetings',
        component: () => import('@/views/meetings/MeetingList.vue'),
        meta: { title: '会议调试台账', permission: 'meeting:view' },
      },
      {
        path: 'meetings/new',
        name: 'meeting-new',
        component: () => import('@/views/meetings/MeetingForm.vue'),
        meta: { title: '新增会议调试', permission: 'meeting:create' },
      },
      {
        path: 'meetings/:id',
        name: 'meeting-detail',
        component: () => import('@/views/meetings/MeetingDetail.vue'),
        meta: { title: '会议详情', permission: 'meeting:view' },
      },
      {
        path: 'meetings/:id/edit',
        name: 'meeting-edit',
        component: () => import('@/views/meetings/MeetingForm.vue'),
        meta: { title: '编辑会议调试', permission: 'meeting:update' },
      },
      {
        path: 'network-assets',
        name: 'network-assets',
        component: () => import('@/views/network-assets/AssetList.vue'),
        meta: { title: 'IP/MAC 台账', permission: 'network_asset:view' },
      },
      {
        path: 'network-assets/new',
        name: 'asset-new',
        component: () => import('@/views/network-assets/AssetForm.vue'),
        meta: { title: '新增 IP/MAC 记录', permission: 'network_asset:create' },
      },
      {
        path: 'network-assets/import',
        name: 'asset-import',
        component: () => import('@/views/network-assets/AssetImport.vue'),
        meta: { title: 'IP/MAC 批量导入', permission: 'network_asset:import' },
      },
      {
        path: 'network-assets/:id',
        name: 'asset-detail',
        component: () => import('@/views/network-assets/AssetDetail.vue'),
        meta: { title: 'IP/MAC 详情', permission: 'network_asset:view' },
      },
      {
        path: 'network-assets/:id/edit',
        name: 'asset-edit',
        component: () => import('@/views/network-assets/AssetForm.vue'),
        meta: { title: '编辑 IP/MAC 记录', permission: 'network_asset:update' },
      },
      {
        path: 'account-batches',
        name: 'account-batches',
        component: () => import('@/views/account-batches/BatchList.vue'),
        meta: { title: '批量账号台账', permission: 'account_batch:view' },
      },
      {
        path: 'account-batches/new',
        name: 'batch-new',
        component: () => import('@/views/account-batches/BatchForm.vue'),
        meta: { title: '新增账号批次', permission: 'account_batch:create' },
      },
      {
        path: 'account-batches/:id',
        name: 'batch-detail',
        component: () => import('@/views/account-batches/BatchDetail.vue'),
        meta: { title: '账号批次详情', permission: 'account_batch:view' },
      },
      {
        path: 'account-batches/:id/import',
        name: 'batch-import',
        component: () => import('@/views/account-batches/BatchImport.vue'),
        meta: { title: '导入账号名单', permission: 'account_batch:import' },
      },
      {
        path: 'maintenance',
        name: 'maintenance',
        component: () => import('@/views/maintenance/MaintenanceList.vue'),
        meta: { title: '通用维护台账', permission: 'maintenance:view' },
      },
      {
        path: 'maintenance/new',
        name: 'maintenance-new',
        component: () => import('@/views/maintenance/MaintenanceForm.vue'),
        meta: { title: '新增维护记录', permission: 'maintenance:create' },
      },
      {
        path: 'maintenance/:id',
        name: 'maintenance-detail',
        component: () => import('@/views/maintenance/MaintenanceDetail.vue'),
        meta: { title: '维护详情', permission: 'maintenance:view' },
      },
      {
        path: 'maintenance/:id/edit',
        name: 'maintenance-edit',
        component: () => import('@/views/maintenance/MaintenanceForm.vue'),
        meta: { title: '编辑维护记录', permission: 'maintenance:update' },
      },
      {
        path: 'system/users',
        name: 'system-users',
        component: () => import('@/views/system/UserList.vue'),
        meta: { title: '用户管理', permission: 'system:user_manage' },
      },
      {
        path: 'system/departments',
        name: 'system-departments',
        component: () => import('@/views/system/DepartmentList.vue'),
        meta: { title: '部门管理', permission: 'system:department_manage' },
      },
      {
        path: 'system/logs',
        name: 'system-logs',
        component: () => import('@/views/system/OperationLogList.vue'),
        meta: { title: '操作日志', permission: 'system:log_view' },
      },
    ],
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/Forbidden.vue'),
    meta: { title: '无访问权限' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const user = useUserStore()

  if (to.meta.public) {
    if (user.isLoggedIn && user.me) return { path: '/dashboard' }
    return true
  }

  if (!user.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (!user.me) {
    try {
      await user.fetchMe()
    } catch {
      user.logout()
      return { path: '/login' }
    }
  }

  const perm = to.meta.permission as string | undefined
  if (perm && !hasPerm(perm)) {
    return { path: '/403' }
  }
  return true
})

export default router
