<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Search, Fold, Expand } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { hasPerm } from '@/utils/permission'
import { categoryGroupOf } from '@/api/types'

const user = useUserStore()
const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const keyword = ref('')

interface MenuItem {
  index: string
  title: string
  icon: string
  permission?: string
}

const navGroups: { title: string; items: MenuItem[] }[] = [
  {
    title: '工作台',
    items: [
      { index: '/dashboard', title: '工作台首页', icon: 'Odometer' },
    ],
  },
  {
    title: '业务台账',
    items: [
      { index: '/meetings', title: '会议调试台账', icon: 'Calendar', permission: 'meeting:view' },
      { index: '/network-assets', title: 'IP/MAC 台账', icon: 'Connection', permission: 'network_asset:view' },
      { index: '/account-batches', title: '批量账号台账', icon: 'Files', permission: 'account_batch:view' },
      { index: 'maintenance:账号类', title: '账号类维护', icon: 'User', permission: 'maintenance:view' },
      { index: 'maintenance:终端类', title: '终端类维护', icon: 'Monitor', permission: 'maintenance:view' },
      { index: 'maintenance:网络类', title: '网络类维护', icon: 'Connection', permission: 'maintenance:view' },
      { index: 'maintenance:无线类', title: '无线类维护', icon: 'Position', permission: 'maintenance:view' },
    ],
  },
  {
    title: '系统管理',
    items: [
      { index: '/system/users', title: '用户管理', icon: 'User', permission: 'system:user_manage' },
      { index: '/system/departments', title: '部门管理', icon: 'OfficeBuilding', permission: 'system:department_manage' },
      { index: '/system/logs', title: '操作日志', icon: 'Document', permission: 'system:log_view' },
    ],
  },
]

function visibleOf(it: MenuItem): MenuItem | null {
  if (it.permission && !hasPerm(it.permission)) return null
  const kw = keyword.value.trim().toLowerCase()
  if (kw && !it.title.toLowerCase().includes(kw)) return null
  return it
}

const groups = computed(() =>
  navGroups
    .map((g) => {
      const items = g.items.map(visibleOf).filter((x): x is MenuItem => x !== null)
      return items.length ? { ...g, items } : null
    })
    .filter((x): x is { title: string; items: MenuItem[] } => x !== null),
)

const activeIndex = computed(() => {
  const p = route.path
  if (p.startsWith('/meetings')) return '/meetings'
  if (p.startsWith('/network-assets')) return '/network-assets'
  if (p.startsWith('/account-batches')) return '/account-batches'
  if (p.startsWith('/maintenance')) {
    const g = (typeof route.query.group === 'string' && route.query.group) || categoryGroupOf(route.query.category as string)
    return `maintenance:${g}`
  }
  if (p.startsWith('/system')) return p
  return p
})

function handleSelect(index: string) {
  if (index.startsWith('maintenance:')) {
    const group = index.slice('maintenance:'.length)
    router.push({ path: '/maintenance', query: { group } })
    return
  }
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
    <el-aside :width="collapsed ? '64px' : '220px'" class="app-aside">
      <div class="brand">
        <span class="brand-dot" />
        <span v-show="!collapsed" class="brand-name">运维智能台账</span>
      </div>
      <div v-show="!collapsed" class="menu-search">
        <el-input v-model="keyword" placeholder="搜索菜单" :prefix-icon="Search" clearable size="small" />
      </div>
      <el-menu
        :default-active="activeIndex"
        :collapse="collapsed"
        :collapse-transition="false"
        class="app-menu"
        @select="handleSelect"
      >
        <template v-for="g in groups" :key="g.title">
          <div v-if="!collapsed" class="menu-group-title">{{ g.title }}</div>
          <el-menu-item v-for="it in g.items" :key="it.index" :index="it.index">
            <el-icon><component :is="it.icon" /></el-icon>
            <template #title>{{ it.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button text :icon="collapsed ? Expand : Fold" @click="collapsed = !collapsed" />
          <span class="header-title">{{ (route.meta.title as string) || '' }}</span>
        </div>
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
  transition: width 0.2s;
  overflow: hidden;
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
  white-space: nowrap;
}
.brand-dot {
  flex: none;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #409eff;
}
.menu-search {
  padding: 0 12px 8px;
}
.menu-group-title {
  padding: 12px 18px 6px;
  font-size: 12px;
  color: #8a94a6;
  letter-spacing: 1px;
  white-space: nowrap;
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
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
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
