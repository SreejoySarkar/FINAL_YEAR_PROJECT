import copy

import pytest

from evoting_crypto import lsag, nizk, paillier


@pytest.fixture(scope="module")
def sk():
    return paillier.generate_keypair(512)


def vote(sk, option, k=4, ctx=b"ctx"):
    pk = sk.public
    plain = [1 if i == option else 0 for i in range(k)]
    enc = [pk.encrypt(m) for m in plain]
    cts, rs = [c for c, _ in enc], [r for _, r in enc]
    return cts, plain, nizk.prove_one_hot(pk, ctx, cts, plain, rs)


def test_paillier_homomorphic(sk):
    pk = sk.public
    a, _ = pk.encrypt(20)
    b, _ = pk.encrypt(22)
    assert sk.decrypt(pk.add(a, b)) == 42


def test_nizk_accepts_valid_and_rejects_wrong_context(sk):
    cts, _, proof = vote(sk, 2)
    assert nizk.verify_one_hot(sk.public, b"ctx", cts, proof)
    assert not nizk.verify_one_hot(sk.public, b"other", cts, proof)


def test_nizk_rejects_overvote_and_tampering(sk):
    pk = sk.public
    cts, _, proof = vote(sk, 1)
    two = [pk.encrypt(m)[0] for m in (1, 1, 0, 0)]
    assert not nizk.verify_one_hot(pk, b"ctx", two, proof)
    big = [pk.encrypt(m)[0] for m in (2, 0, 0, 0)]
    assert not nizk.verify_one_hot(pk, b"ctx", big, proof)
    bad = copy.deepcopy(proof)
    bad["sum_proof"]["z"] = "1"
    assert not nizk.verify_one_hot(pk, b"ctx", cts, bad)
    assert not nizk.verify_one_hot(pk, b"ctx", cts, {"bit_proofs": "x"})
    with pytest.raises(ValueError):
        nizk.prove_one_hot(pk, b"ctx", two, [1, 1, 0, 0], [1, 1, 1, 1])


def test_lsag_sign_verify_and_linkability():
    keys = [lsag.generate_keypair() for _ in range(5)]
    ring_hex = sorted(k[1] for k in keys)
    ring = [lsag.decompress(h) for h in ring_hex]
    x, y = keys[1]
    i = ring_hex.index(y)
    s1 = lsag.sign(b"m1", ring, i, x, "e1")
    s2 = lsag.sign(b"m2", ring, i, x, "e1")
    assert lsag.verify(b"m1", ring, s1, "e1")
    assert not lsag.verify(b"m2", ring, s1, "e1")
    assert not lsag.verify(b"m1", ring, s1, "e2")
    assert s1["key_image"] == s2["key_image"]                         # linkable inside one election
    assert lsag.sign(b"m1", ring, i, x, "e2")["key_image"] != s1["key_image"]  # unlinkable across elections
    other = lsag.sign(b"m1", ring, ring_hex.index(keys[0][1]), keys[0][0], "e1")
    assert other["key_image"] != s1["key_image"]


def test_lsag_rejects_outsider():
    keys = [lsag.generate_keypair() for _ in range(4)]
    ring = [lsag.decompress(k[1]) for k in keys]
    x, _ = lsag.generate_keypair()
    with pytest.raises(ValueError):
        lsag.sign(b"m", ring, 0, x, "e1")


def test_proof_of_possession():
    x, y = lsag.generate_keypair()
    _, y2 = lsag.generate_keypair()
    proof = lsag.prove_possession(x, "ctx")
    assert lsag.verify_possession(y, "ctx", proof)
    assert not lsag.verify_possession(y2, "ctx", proof)
