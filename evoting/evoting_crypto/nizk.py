"""Fiat-Shamir NIZK proofs that a Paillier-encrypted ballot is a valid one-hot vector.

Statement proven for ciphertexts c_0..c_{k-1}:
  1. every c_i encrypts 0 or 1            (OR-proof of n-th residuosity, Cramer-Damgard-Schoenmakers)
  2. the product of all c_i encrypts 1    (Sigma-protocol for an n-th root)
Together: exactly one option is selected.  The `context` (election, ballot definition,
key image) is hashed into every challenge so a proof cannot be copied to another ballot.
"""
import secrets
from math import gcd

from . import hashing
from .paillier import PaillierPublicKey

CHALLENGE_BITS = 128
_MOD = 1 << CHALLENGE_BITS
_DOM_BIT = "evoting/nizk/paillier-bit/v1"
_DOM_SUM = "evoting/nizk/paillier-sum/v1"
MAX_OPTIONS = 64


class ProofError(ValueError):
    pass


def _hx(x: int) -> str:
    return format(x, "x")


def _parse(value, max_bits: int) -> int:
    if not isinstance(value, str) or not value or len(value) > max_bits // 4 + 1:
        raise ProofError("malformed value")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise ProofError("malformed value") from exc


def _is_unit(x: int, pk: PaillierPublicKey) -> bool:
    return 0 < x < pk.n_sq and gcd(x, pk.n) == 1


def _rand_unit(pk: PaillierPublicKey) -> int:
    """Uniform element of Z*_{n^2}. Must span the FULL range, otherwise simulated and
    real transcripts are distinguishable and the proof leaks the bit."""
    while True:
        x = secrets.randbelow(pk.n_sq - 1) + 1
        if gcd(x, pk.n) == 1:
            return x


def _g_inv(pk: PaillierPublicKey) -> int:
    return (1 - pk.n) % pk.n_sq  # (1+n)(1-n) = 1 mod n^2


def _challenge(domain, pk, context, *items) -> int:
    return hashing.hash_to_int(domain, pk.n, context, *items, bits=CHALLENGE_BITS)


def _product(values, modulus) -> int:
    acc = 1
    for v in values:
        acc = acc * v % modulus
    return acc


def prove_one_hot(pk: PaillierPublicKey, context: bytes, ciphertexts, plaintexts, randomness) -> dict:
    if not (len(ciphertexts) == len(plaintexts) == len(randomness)) or not 2 <= len(ciphertexts) <= MAX_OPTIONS:
        raise ValueError("bad ballot dimensions")
    if sorted(plaintexts) != [0] * (len(plaintexts) - 1) + [1]:
        raise ValueError("plaintexts must be one-hot")
    n, n_sq, g_inv = pk.n, pk.n_sq, _g_inv(pk)
    bit_proofs = []
    for idx, (c, m, r) in enumerate(zip(ciphertexts, plaintexts, randomness)):
        u = [c % n_sq, c * g_inv % n_sq]          # u[b] is an n-th power iff m == b
        real, sim = m, 1 - m
        a, e, z = [0, 0], [0, 0], [0, 0]
        s = _rand_unit(pk)
        a[real] = pow(s, n, n_sq)
        e[sim] = secrets.randbelow(_MOD)
        z[sim] = _rand_unit(pk)
        a[sim] = pow(z[sim], n, n_sq) * pow(u[sim], -e[sim], n_sq) % n_sq
        ch = _challenge(_DOM_BIT, pk, context, idx, c, a[0], a[1])
        e[real] = (ch - e[sim]) % _MOD
        z[real] = s * pow(r, e[real], n_sq) % n_sq
        bit_proofs.append({"a0": _hx(a[0]), "a1": _hx(a[1]), "e0": _hx(e[0]), "z0": _hx(z[0]), "z1": _hx(z[1])})
    total_c = _product(ciphertexts, n_sq)
    total_r = _product(randomness, n_sq)
    s = _rand_unit(pk)
    a = pow(s, n, n_sq)
    ch = _challenge(_DOM_SUM, pk, context, total_c, a)
    z = s * pow(total_r, ch, n_sq) % n_sq
    return {"bit_proofs": bit_proofs, "sum_proof": {"a": _hx(a), "z": _hx(z)}}


def verify_one_hot(pk: PaillierPublicKey, context: bytes, ciphertexts, proof) -> bool:
    try:
        return _verify(pk, context, ciphertexts, proof)
    except (ProofError, KeyError, TypeError, ValueError):
        return False


def _verify(pk, context, ciphertexts, proof) -> bool:
    n, n_sq, g_inv = pk.n, pk.n_sq, _g_inv(pk)
    bits = n_sq.bit_length()
    if not 2 <= len(ciphertexts) <= MAX_OPTIONS:
        return False
    bit_proofs = proof["bit_proofs"]
    if len(bit_proofs) != len(ciphertexts) or not _is_unit_all(ciphertexts, pk):
        return False
    for idx, (c, bp) in enumerate(zip(ciphertexts, bit_proofs)):
        a0, a1 = _parse(bp["a0"], bits), _parse(bp["a1"], bits)
        z0, z1 = _parse(bp["z0"], bits), _parse(bp["z1"], bits)
        e0 = _parse(bp["e0"], CHALLENGE_BITS)
        if e0 >= _MOD or not all(_is_unit(v, pk) for v in (a0, a1, z0, z1)):
            return False
        e1 = (_challenge(_DOM_BIT, pk, context, idx, c, a0, a1) - e0) % _MOD
        u0, u1 = c % n_sq, c * g_inv % n_sq
        if pow(z0, n, n_sq) != a0 * pow(u0, e0, n_sq) % n_sq:
            return False
        if pow(z1, n, n_sq) != a1 * pow(u1, e1, n_sq) % n_sq:
            return False
    total_c = _product(ciphertexts, n_sq)
    a = _parse(proof["sum_proof"]["a"], bits)
    z = _parse(proof["sum_proof"]["z"], bits)
    if not (_is_unit(a, pk) and _is_unit(z, pk)):
        return False
    ch = _challenge(_DOM_SUM, pk, context, total_c, a)
    v = total_c * g_inv % n_sq
    return pow(z, n, n_sq) == a * pow(v, ch, n_sq) % n_sq


def _is_unit_all(values, pk) -> bool:
    return all(isinstance(v, int) and _is_unit(v, pk) for v in values)
