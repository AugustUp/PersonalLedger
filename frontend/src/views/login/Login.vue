<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await user.login(form.username.trim(), form.password)
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/dashboard'
      router.push(redirect)
    } catch {
      /* handled by interceptor */
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg decor-1" />
    <div class="login-bg decor-2" />
    <el-card class="login-card" shadow="always">
      <div class="login-head">
        <div class="login-logo">
          <el-icon><Tools /></el-icon>
        </div>
        <h2>运维智能台账系统</h2>
        <p class="login-sub">FastAPI · SQLite · Vue 3</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="'User'" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="密码"
            :prefix-icon="'Lock'"
          />
        </el-form-item>
        <el-button type="primary" size="large" :loading="loading" class="login-btn" @click="onSubmit">
          登 录
        </el-button>
      </el-form>
      <p class="login-tip">默认管理员账号 admin / admin123，请登录后及时修改密码。</p>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #25406b 55%, #2563eb 130%);
  overflow: hidden;
}
.login-bg {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  opacity: 0.35;
  pointer-events: none;
}
.decor-1 {
  width: 420px;
  height: 420px;
  top: -120px;
  left: -80px;
  background: radial-gradient(circle at 30% 30%, #4f8df9, transparent 70%);
}
.decor-2 {
  width: 520px;
  height: 520px;
  bottom: -180px;
  right: -120px;
  background: radial-gradient(circle at 60% 60%, #38bdf8, transparent 70%);
}
.login-card {
  width: 380px;
  border-radius: 14px;
  z-index: 1;
}
.login-head {
  text-align: center;
  margin-bottom: 18px;
}
.login-logo {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #38bdf8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.login-head h2 {
  margin: 0;
  font-size: 20px;
}
.login-sub {
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
}
.login-btn {
  width: 100%;
}
.login-tip {
  margin-top: 14px;
  text-align: center;
  color: #a8abb2;
  font-size: 12px;
}
</style>
