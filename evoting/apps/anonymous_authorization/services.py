import secrets

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.utils import pseudonym
from apps.qr_validation.models import QRToken
from apps.qr_validation.services import validate_token
from apps.voter_authorization.services import authorize_voter
from evoting_crypto import hashing, lsag

from .models import AuthorizationCredential


def pop_context(election_id) -> str:
    return f"evoting/pop/{election_id}"


def issue_credential(*, token: str, public_key_hex: str, possession_proof: dict) -> AuthorizationCredential:
    """QR token + eligibility -> one anonymous public key.

    The token is consumed in the same transaction, so a voter can register exactly one key.
    The credential row is stored WITHOUT any voter reference."""
    try:
        canonical = lsag.normalize(public_key_hex)
    except ValueError:
        raise ApiError("INVALID_PUBLIC_KEY", "Public key is not a valid compressed secp256k1 point.", 400)

    with transaction.atomic():
        qr = validate_token(token, for_update=True)
        voter, election = qr.voter, qr.election
        authorize_voter(voter, election, for_update=True)  # also serialises concurrent attempts per voter
        if QRToken.objects.filter(voter=voter, election=election, is_used=True).exists():
            raise ApiError("ALREADY_REGISTERED", "This voter has already registered for the election.", 409)
        if not lsag.verify_possession(canonical, pop_context(election.pk), possession_proof):
            raise ApiError("INVALID_POSSESSION_PROOF", "Proof of possession of the private key failed.", 400)
        qr.is_used, qr.used_at = True, timezone.now()
        qr.save(update_fields=["is_used", "used_at"])
        try:
            with transaction.atomic():
                credential = AuthorizationCredential.objects.create(
                    election=election, credential_reference=secrets.token_hex(16), public_key=canonical)
        except IntegrityError:
            raise ApiError("PUBLIC_KEY_ALREADY_REGISTERED", "This public key is already registered.", 409)

    log_event("QR_TOKEN_CONSUMED", election=election, actor=f"voter:{pseudonym(voter.pk)}")
    log_event("CREDENTIAL_ISSUED", election=election, actor="system",
              details={"credential_reference": credential.credential_reference})
    return credential


def get_ring_hex(election) -> list[str]:
    """Canonical ring: ACTIVE public keys sorted lexicographically (order leaks nothing)."""
    return sorted(AuthorizationCredential.objects.filter(
        election=election, status=AuthorizationCredential.ACTIVE).values_list("public_key", flat=True))


def get_ring(election) -> list:
    return [lsag.decompress(h) for h in get_ring_hex(election)]


def ring_hash(ring_hex: list[str]) -> str:
    return hashing.sha256_hex("evoting/ring/v1", *ring_hex)
