"""Paillier additively-homomorphic encryption (g = n + 1), pure Python."""
import secrets
from dataclasses import dataclass
from functools import cached_property
from math import gcd

_SMALL_PRIMES = [p for p in range(3, 2000) if all(p % q for q in range(2, int(p ** 0.5) + 1))]


def is_probable_prime(n: int, rounds: int = 40) -> bool:
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int) -> int:
    while True:
        candidate = secrets.randbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if is_probable_prime(candidate):
            return candidate


@dataclass(frozen=True)
class PaillierPublicKey:
    n: int

    @cached_property
    def n_sq(self) -> int:
        return self.n * self.n

    @property
    def bits(self) -> int:
        return self.n.bit_length()

    def random_r(self) -> int:
        while True:
            r = secrets.randbelow(self.n - 1) + 1
            if gcd(r, self.n) == 1:
                return r

    def encrypt(self, m: int, r: int | None = None) -> tuple[int, int]:
        """Returns (ciphertext, randomness). Randomness is needed for the NIZK proof."""
        if not 0 <= m < self.n:
            raise ValueError("plaintext out of range")
        r = r or self.random_r()
        c = (1 + m * self.n) * pow(r, self.n, self.n_sq) % self.n_sq
        return c, r

    def add(self, c1: int, c2: int) -> int:
        return c1 * c2 % self.n_sq

    def to_dict(self) -> dict:
        return {"n": format(self.n, "x")}

    @classmethod
    def from_dict(cls, data: dict) -> "PaillierPublicKey":
        return cls(int(data["n"], 16))


@dataclass(frozen=True)
class PaillierPrivateKey:
    p: int
    q: int

    @cached_property
    def public(self) -> PaillierPublicKey:
        return PaillierPublicKey(self.p * self.q)

    @cached_property
    def lam(self) -> int:
        a, b = self.p - 1, self.q - 1
        return a * b // gcd(a, b)

    @cached_property
    def mu(self) -> int:
        return pow(self.lam, -1, self.public.n)

    def decrypt(self, c: int) -> int:
        n, n_sq = self.public.n, self.public.n_sq
        if not 0 < c < n_sq or gcd(c, n) != 1:
            raise ValueError("invalid ciphertext")
        u = pow(c, self.lam, n_sq)
        return ((u - 1) // n) * self.mu % n

    def to_dict(self) -> dict:
        return {"p": format(self.p, "x"), "q": format(self.q, "x")}

    @classmethod
    def from_dict(cls, data: dict) -> "PaillierPrivateKey":
        return cls(int(data["p"], 16), int(data["q"], 16))


def generate_keypair(bits: int = 2048) -> PaillierPrivateKey:
    if bits < 512 or bits % 2:
        raise ValueError("key size must be an even number >= 512")
    half = bits // 2
    while True:
        p, q = generate_prime(half), generate_prime(half)
        if p != q and gcd(p * q, (p - 1) * (q - 1)) == 1:
            return PaillierPrivateKey(p, q)
