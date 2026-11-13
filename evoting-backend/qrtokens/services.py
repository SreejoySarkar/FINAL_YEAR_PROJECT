import hashlib
import io

import qrcode
from django.conf import settings
from django.core import signing
from django.core.files.base import ContentFile

from .models import QRToken


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def make_signed_token(jti, election_id, voter_id) -> str:
    return signing.dumps(
        {"jti": str(jti), "eid": election_id, "vid": voter_id},
        key=settings.QR_SIGNING_KEY,
        salt=settings.QR_TOKEN_SALT,
    )


def read_signed_token(token: str, max_age_seconds=None):
    """Person 2 uses this to verify a signed QR token."""
    return signing.loads(
        token,
        key=settings.QR_SIGNING_KEY,
        salt=settings.QR_TOKEN_SALT,
        max_age=max_age_seconds,
    )


def issue_token(election, voter) -> QRToken:
    token_row = QRToken(
        election=election,
        voter=voter,
        expires_at=election.end_time,
    )

    token = make_signed_token(
        token_row.jti,
        election.id,
        voter.id,
    )

    token_row.token_hash = hash_token(token)

    img = qrcode.make(token)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    token_row.qr_image.save(
        f"e{election.id}_v{voter.id}_{token_row.jti}.png",
        ContentFile(buf.getvalue()),
        save=False,
    )

    token_row.save()
    return token_row