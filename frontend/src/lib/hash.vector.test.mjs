// Shared canonicalization vector. Mirrored in backend/tests/test_canonical_vector.py: edit both together.
// Run: node --experimental-strip-types src/lib/hash.vector.test.mjs  (imports the real hash.ts, not a copy)
import assert from 'node:assert/strict'
import { canonicalJson, sha256Hex } from './hash.ts'

const VECTOR = {
  z: 1,
  a: { 'é': 'héllo ✓', list: [3, { b: null, a: true }] },
  cents: 8999,
  price: '89.99',
  m: [],
}
const EXPECTED_CANONICAL = '{"a":{"list":[3,{"a":true,"b":null}],"é":"héllo ✓"},"cents":8999,"m":[],"price":"89.99","z":1}'
const EXPECTED_SHA256 = 'f7402f39a40085910d41c9c2fe764b2128fc7b812c3346417159d7d5c4983d31'

assert.equal(canonicalJson(VECTOR), EXPECTED_CANONICAL)
assert.equal(await sha256Hex(EXPECTED_CANONICAL), EXPECTED_SHA256)
assert.throws(() => canonicalJson({ total_cents: 89.99 }), /non-integer/)
assert.doesNotThrow(() => canonicalJson({ product_snapshot: { rating: 4.5 } }))
console.log('hash vector OK')
