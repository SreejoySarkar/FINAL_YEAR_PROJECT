"""Storage of the Paillier PRIVATE key outside PostgreSQL.

The key is encrypted with Fernet (AES-128-CBC + HMAC) under a key derived from a
passphrase with scrypt, and written to a 0600 file in KEY_STORE_DIR.
In production replace this with an HSM / cloud KMS, and split the passphrase between
several election officials (e.g. Shamir secret sharing).
"""
import base64
import hashlib
import json
import os
import re
import secrets
from pathlib import Path

from .paillier import PaillierPrivateKey

_REF_RE = re.compile(r"^ek_[0-9a-f]{16}$")


def new_key_reference() -> str:
    return "ek_" + secrets.token_hex(8)


def _path(directory, key_reference: str) -> Path:
    if not _REF_RE.match(key_reference):
        raise ValueError("invalid key reference")
    return Path(directory) / f"{key_reference}.key"


def _fernet(passphrase: str, salt: bytes):
    from cryptography.fernet import Fernet

    raw = hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return Fernet(base64.urlsafe_b64encode(raw))


def store_private_key(key: PaillierPrivateKey, key_reference: str, passphrase: str, directory) -> Path:
    if not passphrase:
        raise ValueError("a passphrase is required")
    path = _path(directory, key_reference)
    path.parent.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    blob = salt + _fernet(passphrase, salt).encrypt(json.dumps(key.to_dict()).encode())
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(blob)
    return path


def load_private_key(key_reference: str, passphrase: str, directory) -> PaillierPrivateKey:
    from cryptography.fernet import InvalidToken

    blob = _path(directory, key_reference).read_bytes()
    try:
        data = _fernet(passphrase, blob[:16]).decrypt(blob[16:])
    except InvalidToken as exc:
        raise PermissionError("wrong passphrase or corrupted key file") from exc
    return PaillierPrivateKey.from_dict(json.loads(data))
