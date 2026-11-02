/**
 * Canonical JSON stringifier (sorts object keys recursively). Mirrors backend app/core/canon.py;
 * the shared vector in hash.vector.test.mjs / test_canonical_vector.py guards drift between them.
 * Non-integer numbers throw (receipts carry integer cents), except inside product_snapshot, which the
 * backend leaves unchecked (third-party raw data).
 * shortcut: key sort is UTF-16 code-unit order (RFC 8785) while Python sorts by code point; they differ
 * only for astral-plane keys, which receipts never contain. Upgrade if keys can be arbitrary user text.
 * shortcut: an integral float such as 1.0 serializes as "1" here but "1.0" in Python; only possible inside
 * product_snapshot.
 */
export function canonicalJson(obj: unknown, path = 'root'): string {
  if (typeof obj === 'number' && !Number.isInteger(obj) && !path.includes('product_snapshot')) {
    throw new Error(`non-integer number at ${path}: money must be integer minor units`)
  }
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj)
  }

  if (Array.isArray(obj)) {
    return '[' + obj.map((v, i) => canonicalJson(v, `${path}[${i}]`)).join(',') + ']'
  }

  const keys = Object.keys(obj as Record<string, unknown>).sort()
  const entries = keys.map((k) => {
    const val = (obj as Record<string, unknown>)[k]
    return JSON.stringify(k) + ':' + canonicalJson(val, `${path}.${k}`)
  })

  return '{' + entries.join(',') + '}'
}

/**
 * Calculates SHA-256 hex string from an object or string. Throws if WebCrypto is unavailable:
 * a non-cryptographic fallback would make an integrity check lie.
 */
export async function sha256Hex(data: unknown): Promise<string> {
  const jsonStr = typeof data === 'string' ? data : canonicalJson(data)
  if (typeof crypto === 'undefined' || !crypto.subtle) {
    throw new Error('WebCrypto (crypto.subtle) is unavailable; use HTTPS or localhost')
  }
  const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(jsonStr))
  return Array.from(new Uint8Array(hashBuffer)).map((b) => b.toString(16).padStart(2, '0')).join('')
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


const SEALED_FIELDS = ['version', 'currency', 'total_cents', 'constraints', 'product_snapshot', 'merchant_quote', 'capture_conditions'] as const

/** Recompute a pasted receipt's hash locally (no network). Throws a readable Error on bad input. */
export async function verifyReceiptJson(raw: string): Promise<{ match: boolean; claimed: string; computed: string }> {
  let body: Record<string, unknown>
  try {
    body = JSON.parse(raw)
  } catch {
    throw new Error('Not valid JSON.')
  }
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('Expected a JSON object.')
  const missing = [...SEALED_FIELDS, 'receipt_hash'].filter((k) => !(k in body))
  if (missing.length) throw new Error(`Missing fields: ${missing.join(', ')}`)
  const sealed = Object.fromEntries(SEALED_FIELDS.map((k) => [k, body[k]]))
  const computed = await sha256Hex(canonicalJson(sealed))
  const claimed = String(body.receipt_hash).replace(/^sha256:/i, '').toLowerCase()
  return { match: claimed === computed, claimed, computed }
}
