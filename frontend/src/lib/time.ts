let demoClockOffsetMs = 0

export function getDemoClockOffsetMs(): number {
  return demoClockOffsetMs
}

export function setDemoClockOffsetDays(days: number): void {
  demoClockOffsetMs = days * 24 * 60 * 60 * 1000
}

export function getNowWithOffset(): Date {
  return new Date(Date.now() + demoClockOffsetMs)
}

export function formatTimeOnly(isoString: string): string {
  try {
    const d = new Date(isoString)
    return d.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return isoString
  }
}

export function formatDateTime(isoString: string): string {
  try {
    const d = new Date(isoString)
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC'
  } catch {
    return isoString
  }
}

export function relativeTime(isoString: string): string {
  try {
    const now = getNowWithOffset().getTime()
    const past = new Date(isoString).getTime()
    const diffSeconds = Math.max(0, Math.floor((now - past) / 1000))

    if (diffSeconds < 5) return 'just now'
    if (diffSeconds < 60) return `${diffSeconds}s ago`
    const diffMinutes = Math.floor(diffSeconds / 60)
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    const diffHours = Math.floor(diffMinutes / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  } catch {
    return 'recently'
  }
}

export interface CountdownResult {
  text: string
  isExpiringSoon: boolean
  isExpired: boolean
}

export function countdown(expirationIso: string | null): CountdownResult {
  if (!expirationIso) {
    return { text: '—', isExpiringSoon: false, isExpired: false }
  }

  try {
    const now = getNowWithOffset().getTime()
    const target = new Date(expirationIso).getTime()
    const diffMs = target - now

    if (diffMs <= 0) {
      return { text: 'Expired', isExpiringSoon: true, isExpired: true }
    }

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    const diffDays = Math.floor(diffHours / 24)
    const remHours = diffHours % 24

    if (diffDays > 0) {
      return {
        text: `${diffDays}d ${remHours}h`,
        isExpiringSoon: false,
        isExpired: false,
      }
    }

    if (diffHours < 24) {
      return {
        text: `${diffHours}h ${diffMinutes}m`,
        isExpiringSoon: true,
        isExpired: false,
      }
    }

    return {
      text: `${diffMinutes}m`,
      isExpiringSoon: true,
      isExpired: false,
    }
  } catch {
    return { text: '—', isExpiringSoon: false, isExpired: false }
  }
}

