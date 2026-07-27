// Permission helpers + v-permission directive (manual 9.5).
import type { App, Directive } from 'vue'
import { useUserStore } from '@/stores/user'

/** Single permission check. Admin passes everything. */
export function hasPerm(perm: string): boolean {
  const user = useUserStore()
  if (user.role === 'admin') return true
  return user.permissions.includes(perm)
}

/** True if the user has ANY of the given permissions. */
export function hasAnyPerm(perms: string[]): boolean {
  return perms.some((p) => hasPerm(p))
}

/** True if the user has ALL of the given permissions. */
export function hasAllPerm(perms: string[]): boolean {
  return perms.every((p) => hasPerm(p))
}

export const permissionDirective: Directive<HTMLElement, string | string[]> = {
  mounted(el, binding) {
    apply(el, binding.value)
  },
  updated(el, binding) {
    apply(el, binding.value)
  },
}

function apply(el: HTMLElement, value: string | string[] | undefined) {
  if (!value) return
  const perms = Array.isArray(value) ? value : [value]
  if (!perms.some((p) => hasPerm(p))) {
    const parent = el.parentNode
    if (parent) parent.removeChild(el)
  }
}

export function setupPermission(app: App) {
  app.directive('permission', permissionDirective)
}
