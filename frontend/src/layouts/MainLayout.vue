<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { Search, Fold, Expand } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useConfigStore } from '@/stores/config'
import { hasPerm } from '@/utils/permission'

const user = useUserStore()
const config = useConfigStore()
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

const navGroups = computed<{ title: string; items: MenuItem[] }[]>(() => {
  const biz: MenuItem[] = [
    { index: '/meetings', title: config.ledgerName('meetings'), icon: 'Calendar', permission: 'meeting:view' },
    { index: '/network-assets', title: config.ledgerName('network_assets'), icon: 'Connection', permission: 'network_asset:view' },
    { index: '/account-batches', title: config.ledgerName('account_batches'), icon: 'Files', permission: 'account_batch:view' },
  ]
  const groupIcons = ['User', 'Monitor', 'Connection', 'Position']
  config.categoryGroups().forEach((g, i) => {
    biz.push({
      index: `maintenance:${g.label}`,
      title: `${g.label}维护`,
      icon: groupIcons[i % groupIcons.length],
      permission: 'maintenance:view',
    })
  })
  return [
    { title: '工作台', items: [{ index: '/dashboard', title: '工作台首页', icon: 'Odometer' }] },
    { title: '业务台账', items: biz },
    {
      title: '系统管理',
      items: [
        { index: '/system/users', title: '用户管理', icon: 'User', permission: 'system:user_manage' },
        { index: '/system/departments', title: '部门管理', icon: 'OfficeBuilding', permission: 'system:department_manage' },
        { index: '/system/logs', title: '操作日志', icon: 'Document', permission: 'system:log_view' },
        { index: '/system/backup', title: '数据备份', icon: 'FolderOpened', permission: 'system:backup_manage' },
        { index: '/system/customization', title: '台账定制', icon: 'Setting', permission: 'system:config_manage' },
      ],
    },
  ]
})

function visibleOf(it: MenuItem): MenuItem | null {
  if (it.permission && !hasPerm(it.permission)) return null
  const kw = keyword.value.trim().toLowerCase()
  if (kw && !it.title.toLowerCase().includes(kw)) return null
  return it
}

const groups = computed(() =>
  navGroups.value
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
    const g = (typeof route.query.group === 'string' && route.query.group) || config.categoryGroupOf(route.query.category as string)
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

const avatarText = computed(() => {
  const name = user.realName || user.me?.username || ''
  return name ? name.slice(0, 1).toUpperCase() : 'U'
})

// 顶栏面包屑（分组 / 当前页面），与页面内大标题形成层级、避免重复
const breadcrumbs = computed(() => {
  const p = route.path
  const t = (route.meta.title as string) || ''
  if (p === '/dashboard') return ['工作台', t || '首页']
  if (p.startsWith('/meetings')) return ['业务台账', config.ledgerName('meetings')]
  if (p.startsWith('/network-assets')) return ['业务台账', config.ledgerName('network_assets')]
  if (p.startsWith('/account-batches')) return ['业务台账', config.ledgerName('account_batches')]
  if (p.startsWith('/maintenance')) {
    const g = typeof route.query.group === 'string' ? route.query.group : ''
    const cat = typeof route.query.category === 'string' ? route.query.category : ''
    return ['业务台账', g ? `${g}维护` : cat || config.ledgerName('maintenance')]
  }
  if (p.startsWith('/system')) return ['系统管理', t]
  return [t]
})

onMounted(() => {
  config.fetch()
})
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
          <el-breadcrumb separator="/" class="header-breadcrumb">
            <el-breadcrumb-item v-for="b in breadcrumbs" :key="b">{{ b }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <div class="user-meta">
            <el-avatar :size="30" class="user-avatar">{{ avatarText }}</el-avatar>
            <span class="user-name">{{ user.realName || user.me?.username }}</span>
            <el-tag size="small" type="info" effect="plain">{{ roleLabel[user.role] || user.role }}</el-tag>
          </div>
          <el-button text type="primary" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
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
  background: var(--el-color-primary);
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
  background: var(--el-color-primary);
  color: #fff;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  height: 56px;
  padding: 0 18px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-breadcrumb {
  font-size: 14px;
}
.header-breadcrumb :deep(.el-breadcrumb__inner) {
  color: #606266;
}
.header-breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #303133;
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
.user-avatar {
  background: var(--el-color-primary-light-5);
  color: #fff;
  font-weight: 600;
}
.user-name {
  font-size: 14px;
  color: #303133;
}
.app-main {
  background: #f5f7fa;
  padding: 18px;
}
</style>
