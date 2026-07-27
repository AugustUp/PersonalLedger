// Shared display helpers (manual 9.6: empty values show "—", dates formatted).

export function fmt(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—'
  return String(v)
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function toDate(v: string | null | undefined): Date | null {
  if (!v) return null
  const d = new Date(v)
  return isNaN(d.getTime()) ? null : d
}

export function fmtDateTime(v: string | null | undefined): string {
  const d = toDate(v)
  if (!d) return '—'
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function fmtDate(v: string | null | undefined): string {
  const d = toDate(v)
  if (!d) return '—'
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function fmtBool(v: boolean | null | undefined): string {
  if (v === null || v === undefined) return '—'
  return v ? '是' : '否'
}

export function fmtSize(bytes: number | null | undefined): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function fmtDuration(start: string | null, end: string | null): string {
  const a = toDate(start)
  const b = toDate(end)
  if (!a || !b) return '—'
  const ms = b.getTime() - a.getTime()
  if (ms < 0) return '—'
  const h = Math.floor(ms / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  if (h > 0) return `${h} 小时 ${m} 分`
  return `${m} 分钟`
}
