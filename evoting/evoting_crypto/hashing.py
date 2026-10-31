"""SHA-256 helpers with unambiguous (length-prefixed), domain-separated encoding."""
import hashlib
import hmac
import json


def _to_bytes(item) -> bytes:
    if isinstance(item, bytes):
        return item
    if isinstance(item, str):
        return item.encode("utf-8")
    if isinstance(item, int) and not isinstance(item, bool):
        if item < 0:
            raise ValueError("negative integers cannot be encoded")
        return item.to_bytes(max(1, (item.bit_length() + 7) // 8), "big")
    raise TypeError(f"cannot hash value of type {type(item)!r}")


def encode(*items) -> bytes:
    """Length-prefix every item so ('ab','c') and ('a','bc') never collide."""
    out = bytearray()
    for item in items:
        data = _to_bytes(item)
        out += len(data).to_bytes(4, "big") + data
    return bytes(out)


def sha256_bytes(*items) -> bytes:
    return hashlib.sha256(encode(*items)).digest()


def sha256_hex(*items) -> str:
    return sha256_bytes(*items).hex()


def hash_to_int(domain: str, *items, bits: int = 256) -> int:
    """Fiat-Shamir style challenge: top `bits` bits of SHA-256(domain, items...)."""
    if not 1 <= bits <= 256:
        raise ValueError("bits must be between 1 and 256")
    digest = hashlib.sha256(encode(domain, *items)).digest()
    return int.from_bytes(digest, "big") >> (256 - bits)


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def hmac_hex(secret, message: str) -> str:
    key = secret.encode("utf-8") if isinstance(secret, str) else secret
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_token(token: str) -> str:
    """Plain SHA-256 used to store QR tokens (the raw token is never stored)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
