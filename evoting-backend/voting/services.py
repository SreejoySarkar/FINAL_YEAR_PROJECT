
import secrets

from django.core import signing
from django.db import transaction
from django.utils import timezone

from elections.models import Candidate
from qrtokens.models import QRToken
from qrtokens.services import hash_token, read_signed_token
from voters.models import Eligibility

from .crypto import encrypt_ballot, integrity_value, receipt_hash
from .models import Ballot

SESSION_SALT = "vote-session"
SESSION_MAX_AGE = 600  # 10 minutes


class VoteError(Exception):
    """A safe, user-facing voting error."""

    def __init__(self, code, message, status=400, election_id=None, voter_id=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.election_id = election_id
        self.voter_id = voter_id


def make_session(row):
    return signing.dumps(
        {
            "jti": str(row.jti),
            "eid": row.election_id,
            "vid": row.voter_id
        },
        salt=SESSION_SALT
    )


def read_session(request):
    raw = request.headers.get("X-Vote-Session")

    if not raw:
        raise VoteError("no_session", "Scan your QR code first.", 401)

    try:
        return signing.loads(
            raw,
            salt=SESSION_SALT,
            max_age=SESSION_MAX_AGE
        )
    except signing.SignatureExpired:
        raise VoteError(
            "session_expired",
            "Session expired. Scan your QR again.",
            401
        )
    except signing.BadSignature:
        raise VoteError("no_session", "Invalid session.", 401)


def _check_state(row, election, elig):
    """Check whether the voter is allowed to vote."""

    ids = {
        "election_id": election.id,
        "voter_id": row.voter_id
    }

    now = timezone.now()

    if elig is None or not elig.is_eligible or not row.voter.is_active:
        raise VoteError(
            "not_eligible",
            "You are not eligible for this election.",
            403,
            **ids
        )

    if elig.has_voted or row.is_used:
        raise VoteError(
            "already_voted",
            "This vote has already been cast.",
            409,
            **ids
        )

    if row.expires_at <= now:
        raise VoteError(
            "expired",
            "This QR code has expired.",
            400,
            **ids
        )

    if election.status != "published" or not (
        election.start_time <= now <= election.end_time
    ):
        raise VoteError(
            "election_not_open",
            "This election is not open for voting.",
            403,
            **ids
        )


def check_token(token, voter_code):
    """Validate the QR token and the voter's identity."""

    try:
        data = read_signed_token(token)
    except signing.BadSignature:
        raise VoteError("invalid", "Invalid QR code.")

    row = (
        QRToken.objects
        .select_related("election", "voter")
        .filter(jti=data.get("jti"))
        .first()
    )

    if (
        row is None
        or row.token_hash != hash_token(token)
        or row.election_id != data.get("eid")
        or row.voter_id != data.get("vid")
    ):
        raise VoteError("invalid", "Invalid QR code.")

    election, voter = row.election, row.voter

    if voter.voter_code != voter_code.strip():
        raise VoteError(
            "identity_mismatch",
            "Voter ID does not match this QR code.",
            403,
            election_id=election.id,
            voter_id=voter.id
        )

    elig = Eligibility.objects.filter(
        voter=voter,
        election=election
    ).first()

    _check_state(row, election, elig)

    return row, election, voter


def authorize(sess, lock=False):
    """Re-check voting authorization."""

    tokens = QRToken.objects.select_related("election", "voter")
    eligibilities = Eligibility.objects.all()

    if lock:
        tokens = tokens.select_for_update(of=("self",))
        eligibilities = eligibilities.select_for_update()

    try:
        row = tokens.get(jti=sess["jti"])
        elig = eligibilities.get(
            voter_id=sess["vid"],
            election_id=sess["eid"]
        )
    except (QRToken.DoesNotExist, Eligibility.DoesNotExist):
        raise VoteError("not_authorized", "Not authorized.", 403)

    _check_state(row, row.election, elig)

    return row, row.election, elig


def cast_vote(sess, candidate_id):
    """Save one encrypted vote atomically."""

    with transaction.atomic():
        row, election, elig = authorize(sess, lock=True)

        if not Candidate.objects.filter(
            pk=candidate_id,
            election=election
        ).exists():
            raise VoteError(
                "bad_candidate",
                "Invalid candidate.",
                400,
                election_id=election.id,
                voter_id=row.voter_id
            )

        receipt = secrets.token_urlsafe(12)

        nonce, ciphertext = encrypt_ballot(
            election.id,
            candidate_id
        )

        Ballot.objects.create(
            election=election,
            nonce=nonce,
            encrypted_ballot=ciphertext,
            integrity_hash=integrity_value(
                election.id,
                nonce,
                ciphertext
            ),
            receipt_hash=receipt_hash(receipt)
        )

        now = timezone.now()

        elig.has_voted = True
        elig.voted_at = now
        elig.save(update_fields=["has_voted", "voted_at"])

        row.is_used = True
        row.used_at = now
        row.save(update_fields=["is_used", "used_at"])

    return receipt, election
