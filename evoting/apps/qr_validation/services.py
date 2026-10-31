import base64
import io
import secrets
from datetime import timedelta

import qrcode
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.utils import pseudonym
from apps.voter_authorization.services import authorize_voter
from evoting_crypto.hashing import hash_token

from .models import QRToken

_SALT = "evoting.qr.v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.QR_SIGNING_SECRET, salt=_SALT)


def render_qr_png_base64(token: str) -> str:
    image = qrcode.make(token, box_size=8, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@transaction.atomic
def issue_qr_token(voter, election, *, actor: str):
    """Signed, expiring token. Only eligible voters, only before voting opens, only once per voter."""
    authorize_voter(voter, election, for_update=True)
    if QRToken.objects.filter(voter=voter, election=election, is_used=True).exists():
        raise ApiError("ALREADY_REGISTERED", "This voter has already registered for the election.", 409)
    now = timezone.now()
    QRToken.objects.filter(voter=voter, election=election, is_used=False, expires_at__gt=now).update(expires_at=now)
    token = _serializer().dumps({"v": str(voter.pk), "e": str(election.pk), "n": secrets.token_hex(8)})
    row = QRToken.objects.create(
        voter=voter, election=election, token_hash=hash_token(token),
        expires_at=now + timedelta(seconds=settings.QR_TOKEN_TTL_SECONDS),
    )
    log_event("QR_TOKEN_ISSUED", election=election, actor=actor,
              details={"voter": pseudonym(voter.pk), "expires_at": row.expires_at.isoformat()})
    return token, row


def validate_token(token, *, for_update: bool = False) -> QRToken:
    """Signature + age + database state. Call inside transaction.atomic() when for_update=True."""
    if not isinstance(token, str) or not token or len(token) > 1024:
        raise ApiError("QR_INVALID", "QR token is invalid.", 400)
    try:
        payload = _serializer().loads(token, max_age=settings.QR_TOKEN_TTL_SECONDS)
    except SignatureExpired:
        raise ApiError("QR_EXPIRED", "QR token has expired.", 410)
    except BadSignature:
        raise ApiError("QR_INVALID", "QR token is invalid.", 400)
    qs = QRToken.objects.select_for_update() if for_update else QRToken.objects.all()
    row = qs.filter(token_hash=hash_token(token)).first()
    if (row is None or not isinstance(payload, dict)
            or str(row.voter_id) != payload.get("v") or str(row.election_id) != payload.get("e")):
        raise ApiError("QR_INVALID", "QR token is invalid.", 400)
    if row.is_used:
        raise ApiError("QR_ALREADY_USED", "QR token has already been used.", 409)
    if row.expires_at <= timezone.now():
        raise ApiError("QR_EXPIRED", "QR token has expired.", 410)
    return row
