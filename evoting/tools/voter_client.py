"""Reference voter client: keys, QR registration and ballot encryption/signing all happen HERE,
so the server never sees the private key or the choice.

    python tools/voter_client.py keygen --election 1 > mykey.json
    python tools/voter_client.py register --election 1 --token <QR token> --key mykey.json
    python tools/voter_client.py vote --election 1 --candidate 2 --key mykey.json
Run from the project root (it reuses the project's crypto package); set EVOTING_URL if not localhost.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from evoting_crypto import lsag  # noqa: E402
from evoting_crypto.paillier import PaillierPublicKey  # noqa: E402,F401
from evoting_crypto import hashing, nizk  # noqa: E402,F401

BASE = os.environ.get("EVOTING_URL", "http://127.0.0.1:8000")


def ballot_payload(election_id, definition_hash, options, paillier_public, ring_hex, x, candidate_id):
    """Pure-Python copy of apps.vote_submission.ballot_builder (no Django import needed)."""
    pk = PaillierPublicKey.from_dict(paillier_public)
    idx = next(o["option_index"] for o in options if o["candidate_id"] == str(candidate_id))
    plain = [1 if o["option_index"] == idx else 0 for o in options]
    enc = [pk.encrypt(m) for m in plain]
    cts, rs = [c for c, _ in enc], [r for _, r in enc]
    image = lsag.key_image(x, election_id)
    ctx = hashing.encode("evoting/ballot-context/v1", str(election_id), definition_hash, image)
    proof = nizk.prove_one_hot(pk, ctx, cts, plain, rs)
    ct_hex = [format(c, "x") for c in cts]
    msg = hashing.encode("evoting/ballot-message/v1", str(election_id), definition_hash, *ct_hex)
    mine = lsag.public_key_of(x)
    sig = lsag.sign(msg, [lsag.decompress(h) for h in ring_hex], ring_hex.index(mine), x, election_id)
    return {"election_id": str(election_id), "ciphertexts": ct_hex, "proof": proof, "ring_signature": sig}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["keygen", "register", "vote"])
    parser.add_argument("--election", required=True)
    parser.add_argument("--key")
    parser.add_argument("--token")
    parser.add_argument("--candidate")
    a = parser.parse_args()

    if a.command == "keygen":
        x, y = lsag.generate_keypair()
        print(json.dumps({"private_key": format(x, "x"), "public_key": y}))
        return
    key = json.loads(Path(a.key).read_text())
    x = int(key["private_key"], 16)
    if a.command == "register":
        body = {"token": a.token, "public_key": key["public_key"],
                "possession_proof": lsag.prove_possession(x, f"evoting/pop/{a.election}")}
        r = requests.post(f"{BASE}/api/anonymous-auth/credentials/", json=body, timeout=30)
    else:
        ballot = requests.get(f"{BASE}/api/ballots/{a.election}/", timeout=30).json()
        ring = requests.get(f"{BASE}/api/anonymous-auth/ring/{a.election}/", timeout=60).json()["public_keys"]
        body = ballot_payload(a.election, ballot["definition_hash"], ballot["options"],
                              ballot["encryption"]["public_key"], ring, x, a.candidate)
        r = requests.post(f"{BASE}/api/votes/submit/", json=body, timeout=120)
    print(r.status_code, json.dumps(r.json(), indent=2))


if __name__ == "__main__":
    main()
