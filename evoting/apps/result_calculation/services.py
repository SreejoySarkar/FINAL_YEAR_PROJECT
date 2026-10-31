from django.conf import settings

from apps.anonymous_storage.models import AnonymousBallot, EncryptedVoteComponent
from apps.audit_management.services import log_event
from apps.ballot_management.services import build_ballot_definition
from apps.common.exceptions import ApiError
from apps.common.integration import CLOSED, election_phase
from apps.election_verification.services import verify_election
from apps.vote_encryption.services import get_active_key
from evoting_crypto import key_management

from .models import ElectionResult


def calculate_result(election, *, actor: str, passphrase: str | None = None) -> ElectionResult:
    """Homomorphic tally: multiply ciphertexts per option, decrypt ONLY the 4-or-so aggregates."""
    if election_phase(election) != CLOSED:
        raise ApiError("ELECTION_NOT_CLOSED", "Results can only be calculated after the election is closed.", 409)
    existing = ElectionResult.objects.filter(election=election).first()
    if existing and existing.published_at:
        raise ApiError("ALREADY_PUBLISHED", "Results are already published.", 409)

    report = verify_election(election, actor=actor)           # also flags/rejects bad ballots
    key = get_active_key(election)
    pk = key.paillier_public_key()
    definition = build_ballot_definition(election)
    count = len(definition["options"])
    aggregates = [1] * count                                   # 1 == Enc(0)
    rows = EncryptedVoteComponent.objects.filter(
        ballot__election=election, ballot__verification_status=AnonymousBallot.VERIFIED
    ).values_list("option_index", "ciphertext").iterator(chunk_size=2000)
    for option_index, ciphertext in rows:
        aggregates[option_index] = pk.add(aggregates[option_index], int(ciphertext, 16))

    secret = passphrase or settings.ELECTION_KEY_PASSPHRASE
    if not secret:
        raise ApiError("PASSPHRASE_REQUIRED", "Key passphrase is required to decrypt the totals.", 400)
    try:
        private = key_management.load_private_key(key.key_reference, secret, settings.KEY_STORE_DIR)
    except PermissionError:
        log_event("TALLY_KEY_ACCESS_DENIED", election=election, actor=actor)
        raise ApiError("KEY_ACCESS_DENIED", "Wrong passphrase.", 403)
    totals = [private.decrypt(a) for a in aggregates]

    valid = report["ballots_verified"]
    consistent = sum(totals) == valid and report["audit_chain_ok"]
    result_data = {
        "definition_hash": definition["hash"],
        "candidates": [{"candidate_id": o["candidate_id"], "label": o["label"], "votes": totals[o["option_index"]]}
                       for o in definition["options"]],
        # anyone can recompute these products from the public ballot data and compare
        "aggregate_ciphertexts": [format(a, "x") for a in aggregates],
    }
    result, _ = ElectionResult.objects.update_or_create(election=election, defaults={
        "result_data": result_data, "valid_ballots": valid, "rejected_ballots": report["ballots_rejected"],
        "verification_status": ElectionResult.VERIFIED if consistent else ElectionResult.FAILED, "published_at": None})
    log_event("RESULT_CALCULATED", election=election, actor=actor,
              details={"valid_ballots": valid, "rejected_ballots": report["ballots_rejected"], "status": result.verification_status})
    return result
