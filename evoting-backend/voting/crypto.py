import base64
import hashlib
import hmac
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings


def election_key(election_id: int) -> bytes:
    """Derive a separate 32-byte key per election from the master key."""
    master = base64.b64decode(settings.BALLOT_MASTER_KEY)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=f"ballot-key-election-{election_id}".encode()
    )
    return hkdf.derive(master)


def encrypt_ballot(election_id: int, candidate_id: int):
    """Returns (nonce, ciphertext). A random pad makes every plaintext unique."""
    nonce = os.urandom(12)
    plaintext = json.dumps({
        "candidate_id": candidate_id,
        "pad": os.urandom(8).hex()
    }).encode()

    aad = str(election_id).encode()
    ciphertext = AESGCM(election_key(election_id)).encrypt(
        nonce, plaintext, aad
    )

    return nonce, ciphertext


def decrypt_ballot(election_id: int, nonce: bytes, ciphertext: bytes) -> int:
    """Raises InvalidTag if the encrypted data was changed."""
    aad = str(election_id).encode()
    plaintext = AESGCM(election_key(election_id)).decrypt(
        nonce, ciphertext, aad
    )
    return json.loads(plaintext)["candidate_id"]


def integrity_value(election_id: int, nonce: bytes, ciphertext: bytes) -> str:
    msg = str(election_id).encode() + b"|" + nonce + b"|" + ciphertext

    return hmac.new(
        settings.INTEGRITY_KEY.encode(),
        msg,
        hashlib.sha256
    ).hexdigest()


def receipt_hash(receipt: str) -> str:
    return hashlib.sha256(receipt.encode()).hexdigest()