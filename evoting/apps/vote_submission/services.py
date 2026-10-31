from apps.anonymous_storage.services import store_ballot
from apps.anonymous_authorization.services import get_ring_hex, ring_hash
from apps.audit_management.services import log_event
from apps.ballot_management.services import build_ballot_definition, signature_message
from apps.common.exceptions import ApiError
from apps.common.integration import VOTING, election_phase, get_election
from apps.duplicate_voting.services import verify_signature_and_check_duplicate
from apps.nizk_proofs.services import verify_ballot_proof
from apps.vote_encryption.services import get_active_key
from evoting_crypto import hashing, lsag


def submit_vote(*, election_id, ciphertexts: list[str], proof: dict, ring_signature: dict) -> dict:
    election = get_election(election_id)
    try:
        return _validate_and_store(election, ciphertexts, proof, ring_signature)
    except ApiError as exc:
        if exc.status_code != 429:
            log_event("VOTE_REJECTED", election=election, actor="anonymous", details={"reason": exc.code})
        raise


def _validate_and_store(election, ciphertexts, proof, ring_signature) -> dict:
    if election_phase(election) != VOTING:
        raise ApiError("VOTING_CLOSED", "Voting is not open for this election.", 409)
    key = get_active_key(election)
    pk = key.paillier_public_key()
    definition = build_ballot_definition(election)
    if len(ciphertexts) != len(definition["options"]):
        raise ApiError("INVALID_BALLOT", "Ciphertext count does not match the number of candidates.", 422)
    try:
        cts = [int(c, 16) for c in ciphertexts]
        image = lsag.normalize(ring_signature["key_image"])
    except (ValueError, KeyError, TypeError):
        raise ApiError("INVALID_BALLOT", "Malformed ciphertext or key image.", 422)
    ct_hex = [format(c, "x") for c in cts]  # canonical encoding, used for signing and storage

    # 1. NIZK: the ciphertexts encode exactly one valid selection (checked before the costlier ring verify)
    if not verify_ballot_proof(pk, election.pk, definition["hash"], image, cts, proof):
        raise ApiError("INVALID_PROOF", "Ballot validity proof failed.", 422)
    # 2. LSAG: signed by SOME registered voter + key image not used before
    message = signature_message(election.pk, definition["hash"], ct_hex)
    key_image = verify_signature_and_check_duplicate(election, message, ring_signature)
    # 3. Atomic store (unique constraint = final duplicate guard)
    ring_h = ring_hash(get_ring_hex(election))
    ballot = store_ballot(
        election=election, election_key=key, key_image=key_image, ring_signature=ring_signature,
        proof_data={"definition_hash": definition["hash"], "ring_hash": ring_h, "proof": proof}, ciphertext_hex=ct_hex)
    log_event("VOTE_ACCEPTED", election=election, actor="anonymous", details={"ballot_id": str(ballot.id)})
    return {"status": "accepted", "ballot_id": str(ballot.id),
            "receipt": hashing.sha256_hex("evoting/receipt/v1", str(ballot.id), *ct_hex)}
