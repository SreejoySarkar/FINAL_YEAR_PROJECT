from apps.common.exceptions import ApiError
from apps.common.integration import candidate_label, get_candidates
from evoting_crypto import hashing
from evoting_crypto.nizk import MAX_OPTIONS


def build_ballot_definition(election) -> dict:
    """Ballot = candidates from Person 1, ordered by primary key; list position = option_index."""
    candidates = get_candidates(election)
    if not 2 <= len(candidates) <= MAX_OPTIONS:
        raise ApiError("BALLOT_NOT_READY", f"An election needs between 2 and {MAX_OPTIONS} candidates.", 409)
    options = [{"option_index": i, "candidate_id": str(c.pk), "label": candidate_label(c)} for i, c in enumerate(candidates)]
    digest = hashing.sha256_hex("evoting/ballot-definition/v1", str(election.pk),
                                hashing.canonical_json([[o["option_index"], o["candidate_id"]] for o in options]))
    return {"election_id": str(election.pk), "options": options, "hash": digest}


def proof_context(election_id, definition_hash: str, key_image: str) -> bytes:
    """Bound into every NIZK challenge. Including the key image stops ballot-copying attacks."""
    return hashing.encode("evoting/ballot-context/v1", str(election_id), definition_hash, key_image)


def signature_message(election_id, definition_hash: str, ciphertext_hex: list[str]) -> bytes:
    """The exact bytes the voter ring-signs: ties the anonymous authorisation to THIS ciphertext set."""
    return hashing.encode("evoting/ballot-message/v1", str(election_id), definition_hash, *ciphertext_hex)
