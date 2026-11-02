/**
 * Canonical JSON stringifier (sorts object keys recursively).
 */
export function canonicalJson(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj)
  }

  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJson).join(',') + ']'
  }

  const keys = Object.keys(obj as Record<string, unknown>).sort()
  const entries = keys.map((k) => {
    const val = (obj as Record<string, unknown>)[k]
    return JSON.stringify(k) + ':' + canonicalJson(val)
  })

  return '{' + entries.join(',') + '}'
}

/**
 * Calculates SHA-256 hex string from an object or string.
 */
export async function sha256Hex(data: unknown): Promise<string> {
  const jsonStr = typeof data === 'string' ? data : canonicalJson(data)
  const encoder = new TextEncoder()
  const bytes = encoder.encode(jsonStr)

  if (typeof crypto !== 'undefined' && crypto.subtle) {
    const hashBuffer = await crypto.subtle.digest('SHA-256', bytes)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
  }

  // Simple synchronous fallback for non-crypto environments
  let hash = 0
  for (let i = 0; i < jsonStr.length; i++) {
    hash = (hash << 5) - hash + jsonStr.charCodeAt(i)
    hash |= 0
  }
  return ('00000000' + (hash >>> 0).toString(16)).slice(-8).repeat(8)
}

/**
 * Truncate hash to 8...4 format, e.g. sha256:8f3b2c1d...9d1a -> sha256:8f3b2c1d…9d1a
 */
export function truncateHash(hashStr: string, prefix = 'sha256:'): string {
  if (!hashStr) return ''
  let clean = hashStr
  let hasPrefix = false
  if (hashStr.startsWith(prefix)) {
    clean = hashStr.slice(prefix.length)
    hasPrefix = true
  }

  if (clean.length <= 12) {
    return hasPrefix ? `${prefix}${clean}` : clean
  }

  const head = clean.slice(0, 8)
  const tail = clean.slice(-4)
  const formatted = `${head}…${tail}`
  return hasPrefix ? `${prefix}${formatted}` : formatted
}

export function truncateId(id: string): string {
  if (!id) return ''
  if (id.length <= 12) return id
  return `${id.slice(0, 8)}…${id.slice(-4)}`
}

