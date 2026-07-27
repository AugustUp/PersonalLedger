<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { hasPerm } from '@/utils/permission'

const user = useUserStore()
const route = useRoute()
const router = useRouter()

interface MenuItem {
  index: string
  title: string
  icon: string
  permission?: string
  children?: MenuItem[]
}

const menu: MenuItem[] = [
  { index: '/dashboard', title: '首页', icon: 'Odometer' },
  { index: '/meetings', title: '会议调试台账', icon: 'Calendar', permission: 'meeting:view' },
  { index: '/network-assets', title: 'IP/MAC 台账', icon: 'Connection', permission: 'network_asset:view' },
  { index: '/account-batches', title: '批量账号台账', icon: 'Files', permission: 'account_batch:view' },
  { index: '/maintenance', title: '通用维护台账', icon: 'Tools', permission: 'maintenance:view' },
  {
    index: '/system',
    title: '系统管理',
    icon: 'Setting',
    children: [
      { index: '/system/users', title: '用户管理', icon: 'User', permission: 'system:user_manage' },
      { index: '/system/departments', title: '部门管理', icon: 'OfficeBuilding', permission: 'system:department_manage' },
      { index: '/system/logs', title: '操作日志', icon: 'Document', permission: 'system:log_view' },
    ],
  },
]

const visibleMenu = computed(() =>
  menu
    .map((g) => {
      if (g.children) {
        const kids = g.children.filter((c) => !c.permission || hasPerm(c.permission))
        return kids.length ? { ...g, children: kids } : null
      }
      return g.permission && !hasPerm(g.permission) ? null : g
    })
    .filter((x): x is MenuItem => x !== null),
)

const activeIndex = computed(() => {
  const p = route.path
  if (p.startsWith('/meetings')) return '/meetings'
  if (p.startsWith('/network-assets')) return '/network-assets'
  if (p.startsWith('/account-batches')) return '/account-batches'
  if (p.startsWith('/maintenance')) return '/maintenance'
  if (p.startsWith('/system')) return p
  return p
})

function handleSelect(index: string) {
  if (index !== route.path) router.push(index)
}

async function onLogout() {
  try {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await user.logout()
  router.push('/login')
}

const roleLabel: Record<string, string> = {
  admin: '系统管理员',
  manager: '运维管理员',
  operator: '普通运维',
}
</script>

<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="app-aside">
      <div class="brand">
        <span class="brand-dot" />
        <span class="brand-name">运维智能台账</span>
      </div>
      <el-menu :default-active="activeIndex" class="app-menu" @select="handleSelect">
        <template v-for="g in visibleMenu" :key="g.index">
          <el-sub-menu v-if="g.children" :index="g.index">
            <template #title>
              <el-icon><component :is="g.icon" /></el-icon>
              <span>{{ g.title }}</span>
            </template>
            <el-menu-item v-for="c in g.children" :key="c.index" :index="c.index">
              <el-icon><component :is="c.icon" /></el-icon>
              <span>{{ c.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="g.index">
            <el-icon><component :is="g.icon" /></el-icon>
            <span>{{ g.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-title">{{ (route.meta.title as string) || '' }}</div>
        <div class="header-right">
          <span class="user-meta">
            {{ user.realName || user.me?.username }}
            <el-tag size="small" type="info" effect="plain">{{ roleLabel[user.role] || user.role }}</el-tag>
          </span>
          <el-button text type="primary" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-aside {
  background: #1f2d3d;
  color: #fff;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 56px;
  padding: 0 18px;
  font-weight: 600;
  font-size: 16px;
  color: #fff;
}
.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
}
.app-menu {
  border-right: none;
  background: #1f2d3d;
}
.app-menu :deep(.el-menu-item),
.app-menu :deep(.el-sub-menu__title) {
  color: #c0c4cc;
}
.app-menu :deep(.el-menu-item.is-active) {
  background: #409eff;
  color: #fff;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}
.header-title {
  font-size: 18px;
  font-weight: 600;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.user-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}
.app-main {
  background: #f5f7fa;
  padding: 18px;
}
</style>
