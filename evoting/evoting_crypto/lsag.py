"""LSAG (Liu-Wei-Wong Linkable Spontaneous Anonymous Group) ring signatures on secp256k1.

* Anyone in the ring can sign; the verifier cannot tell who.
* The key image I = x * H(election_id) is identical for every signature made with the same
  secret key *in the same election* -> a second ballot from the same voter is detectable,
  while images from different elections are unlinkable.
Pure Python (Jacobian coordinates). Fine for a project; swap in libsecp256k1 for scale.
"""
import secrets
from itertools import count

from . import hashing

P = 2 ** 256 - 2 ** 32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
)
MAX_RING = 20000
_INF = (0, 1, 0)


# ---------------------------------------------------------------- curve arithmetic
def _jdouble(pt):
    x1, y1, z1 = pt
    if z1 == 0 or y1 == 0:
        return _INF
    s = 4 * x1 * y1 * y1 % P
    m = 3 * x1 * x1 % P
    x3 = (m * m - 2 * s) % P
    y3 = (m * (s - x3) - 8 * pow(y1, 4, P)) % P
    return x3, y3, 2 * y1 * z1 % P


def _jadd(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    if z1 == 0:
        return p2
    if z2 == 0:
        return p1
    z1z1, z2z2 = z1 * z1 % P, z2 * z2 % P
    u1, u2 = x1 * z2z2 % P, x2 * z1z1 % P
    s1, s2 = y1 * z2 * z2z2 % P, y2 * z1 * z1z1 % P
    if u1 == u2:
        return _jdouble(p1) if s1 == s2 else _INF
    h, r = (u2 - u1) % P, (s2 - s1) % P
    h2 = h * h % P
    h3 = h * h2 % P
    v = u1 * h2 % P
    x3 = (r * r - h3 - 2 * v) % P
    y3 = (r * (v - x3) - s1 * h3) % P
    return x3, y3, h * z1 * z2 % P


def _to_jac(pt):
    return _INF if pt is None else (pt[0], pt[1], 1)


def _to_affine(pt):
    x, y, z = pt
    if z == 0:
        return None
    zi = pow(z, -1, P)
    zi2 = zi * zi % P
    return x * zi2 % P, y * zi2 * zi % P


def point_mul(k: int, pt):
    """k * pt (affine in, affine out; None = point at infinity). Curve has cofactor 1."""
    k %= N
    result, addend = _INF, _to_jac(pt)
    while k:
        if k & 1:
            result = _jadd(result, addend)
        addend = _jdouble(addend)
        k >>= 1
    return _to_affine(result)


def point_add(p1, p2):
    return _to_affine(_jadd(_to_jac(p1), _to_jac(p2)))


def is_on_curve(pt) -> bool:
    if pt is None:
        return False
    x, y = pt
    return 0 <= x < P and 0 <= y < P and (y * y - x * x * x - 7) % P == 0


# ---------------------------------------------------------------- encoding
def compress(pt) -> str:
    if pt is None:
        return "00"
    return ("02" if pt[1] % 2 == 0 else "03") + pt[0].to_bytes(32, "big").hex()


def decompress(h: str):
    """Parse a 33-byte compressed point; raises ValueError for anything invalid."""
    if not isinstance(h, str) or len(h) != 66 or h[:2] not in ("02", "03"):
        raise ValueError("invalid point encoding")
    try:
        x = int(h[2:], 16)
    except ValueError as exc:
        raise ValueError("invalid point encoding") from exc
    if x >= P:
        raise ValueError("invalid point encoding")
    rhs = (x ** 3 + 7) % P
    y = pow(rhs, (P + 1) // 4, P)
    if y * y % P != rhs:
        raise ValueError("point not on curve")
    if (y % 2 == 0) != (h[:2] == "02"):
        y = P - y
    return x, y


def normalize(h: str) -> str:
    return compress(decompress(h))


# ---------------------------------------------------------------- keys & hashing
def generate_keypair() -> tuple[int, str]:
    x = secrets.randbelow(N - 1) + 1
    return x, compress(point_mul(x, G))


def public_key_of(x: int) -> str:
    return compress(point_mul(x, G))


def hash_to_point(data: bytes):
    for ctr in count():
        x = hashing.hash_to_int("evoting/lsag/h2c", data, ctr) % P
        rhs = (x ** 3 + 7) % P
        y = pow(rhs, (P + 1) // 4, P)
        if y * y % P == rhs:
            return x, (y if y % 2 == 0 else P - y)


def key_image_base(election_id) -> tuple:
    return hash_to_point(b"evoting/lsag/key-image-base/" + str(election_id).encode())


def key_image(x: int, election_id) -> str:
    return compress(point_mul(x, key_image_base(election_id)))


def ring_digest(ring) -> bytes:
    return hashing.sha256_bytes(*[compress(p) for p in ring])


def _challenge(message: bytes, digest: bytes, img, left, right) -> int:
    return hashing.hash_to_int(
        "evoting/lsag/challenge", message, digest, compress(img), compress(left), compress(right)
    ) % N


# ---------------------------------------------------------------- sign / verify
def sign(message: bytes, ring: list, signer_index: int, x: int, election_id) -> dict:
    n = len(ring)
    if not 2 <= n <= MAX_RING or not 0 <= signer_index < n:
        raise ValueError("bad ring")
    if point_mul(x, G) != ring[signer_index]:
        raise ValueError("secret key does not match ring position")
    h = key_image_base(election_id)
    img = point_mul(x, h)
    digest = ring_digest(ring)
    c, s = [0] * n, [0] * n
    u = secrets.randbelow(N - 1) + 1
    c[(signer_index + 1) % n] = _challenge(message, digest, img, point_mul(u, G), point_mul(u, h))
    i = (signer_index + 1) % n
    while i != signer_index:
        s[i] = secrets.randbelow(N - 1) + 1
        left = point_add(point_mul(s[i], G), point_mul(c[i], ring[i]))
        right = point_add(point_mul(s[i], h), point_mul(c[i], img))
        c[(i + 1) % n] = _challenge(message, digest, img, left, right)
        i = (i + 1) % n
    s[signer_index] = (u - c[signer_index] * x) % N
    return {"key_image": compress(img), "c0": format(c[0], "x"), "s": [format(v, "x") for v in s]}


def verify(message: bytes, ring: list, signature: dict, election_id) -> bool:
    try:
        n = len(ring)
        if not 2 <= n <= MAX_RING or len(set(ring)) != n or not all(is_on_curve(p) for p in ring):
            return False
        img = decompress(signature["key_image"])
        s_vals = [int(v, 16) for v in signature["s"]]
        c0 = int(signature["c0"], 16)
        if len(s_vals) != n or not 0 <= c0 < N or any(not 0 <= v < N for v in s_vals):
            return False
        h = key_image_base(election_id)
        digest = ring_digest(ring)
        c = c0
        for i in range(n):
            left = point_add(point_mul(s_vals[i], G), point_mul(c, ring[i]))
            right = point_add(point_mul(s_vals[i], h), point_mul(c, img))
            c = _challenge(message, digest, img, left, right)
        return c == c0
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


# ---------------------------------------------------------------- proof of possession
def prove_possession(x: int, context: str) -> dict:
    """Schnorr proof that the registrant knows the secret key (stops rogue-key ring attacks)."""
    y = point_mul(x, G)
    k = secrets.randbelow(N - 1) + 1
    r = point_mul(k, G)
    e = hashing.hash_to_int("evoting/lsag/pop", context, compress(y), compress(r)) % N
    return {"R": compress(r), "s": format((k + e * x) % N, "x")}


def verify_possession(public_key_hex: str, context: str, proof: dict) -> bool:
    try:
        y, r = decompress(public_key_hex), decompress(proof["R"])
        s = int(proof["s"], 16)
        if not 0 < s < N:
            return False
        e = hashing.hash_to_int("evoting/lsag/pop", context, compress(y), compress(r)) % N
        return point_mul(s, G) == point_add(r, point_mul(e, y))
    except (KeyError, TypeError, ValueError):
        return False
