"""Shared canonicalization vector. Mirrored in frontend/src/lib/hash.vector.test.mjs: edit both together."""

from app.core.canon import canonical_json, sha256_hex

VECTOR = {
    "z": 1,
    "a": {"é": "héllo ✓", "list": [3, {"b": None, "a": True}]},
    "cents": 8999,
    "price": "89.99",
    "m": [],
}
EXPECTED_CANONICAL = '{"a":{"list":[3,{"a":true,"b":null}],"é":"héllo ✓"},"cents":8999,"m":[],"price":"89.99","z":1}'
EXPECTED_SHA256 = "f7402f39a40085910d41c9c2fe764b2128fc7b812c3346417159d7d5c4983d31"


def test_backend_matches_shared_vector():
    assert canonical_json(VECTOR) == EXPECTED_CANONICAL
    assert sha256_hex(EXPECTED_CANONICAL) == EXPECTED_SHA256
