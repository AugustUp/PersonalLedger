// Pinia user store: token persistence, profile + permissions, login/logout/me.
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { get, post } from '@/api/http'
import type { UserMe } from '@/api/types'

const TOKEN_KEY = 'ops_ledger_token'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const me = ref<UserMe | null>(null)

  const permissions = computed<string[]>(() => me.value?.permissions ?? [])
  const role = computed<string>(() => me.value?.role ?? '')
  const realName = computed<string>(() => me.value?.real_name ?? '')
  const isLoggedIn = computed<boolean>(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  }

  async function login(username: string, password: string) {
    const data = await post<{ access_token: string; expires_in: number }>('/auth/login', {
      username,
      password,
    })
    setToken(data.access_token)
    await fetchMe()
  }

  async function fetchMe(): Promise<UserMe> {
    const data = await get<UserMe>('/auth/me')
    me.value = data
    return data
  }

  async function logout() {
    try {
      await post('/auth/logout', {})
    } catch {
      /* ignore network errors on logout */
    }
    setToken('')
    me.value = null
  }

  return { token, me, permissions, role, realName, isLoggedIn, setToken, login, fetchMe, logout }
})
