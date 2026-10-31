from apps.anonymous_authorization.models import AuthorizationCredential
from apps.anonymous_authorization.services import get_ring, get_ring_hex, ring_hash
from apps.anonymous_storage.models import AnonymousBallot
from apps.audit_management.services import log_event, verify_chain
from apps.ballot_management.services import build_ballot_definition, signature_message
from apps.nizk_proofs.services import verify_ballot_proof
from apps.vote_encryption.services import get_active_key
from evoting_crypto import lsag


def verify_ballot(ballot, pk, election, definition, ring, ring_h) -> str | None:
    """Independent re-verification of one stored ballot. Returns a failure reason or None."""
    comps = sorted(ballot.components.all(), key=lambda c: c.option_index)
    if [c.option_index for c in comps] != list(range(len(definition["options"]))):
        return "BAD_COMPONENTS"
    data = ballot.proof_data or {}
    if data.get("definition_hash") != definition["hash"]:
        return "DEFINITION_MISMATCH"
    if data.get("ring_hash") != ring_h:
        return "RING_MISMATCH"
    ct_hex = [c.ciphertext for c in comps]
    try:
        cts = [int(c, 16) for c in ct_hex]
    except ValueError:
        return "BAD_CIPHERTEXT"
    if ballot.ring_signature.get("key_image") is None or lsag.normalize(ballot.ring_signature["key_image"]) != ballot.key_image:
        return "KEY_IMAGE_MISMATCH"
    if not verify_ballot_proof(pk, election.pk, definition["hash"], ballot.key_image, cts, data.get("proof", {})):
        return "INVALID_PROOF"
    if not lsag.verify(signature_message(election.pk, definition["hash"], ct_hex), ring, ballot.ring_signature, election.pk):
        return "INVALID_SIGNATURE"
    return None


def verify_election(election, actor: str = "system") -> dict:
    """Re-checks every stored ballot (NIZK + LSAG + ring + key-image uniqueness) and the audit chain."""
    pk = get_active_key(election).paillier_public_key()
    definition = build_ballot_definition(election)
    ring_hex = get_ring_hex(election)
    ring, ring_h = get_ring(election), ring_hash(ring_hex)
    verified, rejected, issues = 0, 0, []
    seen_images = set()
    for ballot in AnonymousBallot.objects.filter(election=election).prefetch_related("components").iterator(chunk_size=200):
        reason = verify_ballot(ballot, pk, election, definition, ring, ring_h)
        if reason is None and ballot.key_image in seen_images:
            reason = "DUPLICATE_KEY_IMAGE"
        seen_images.add(ballot.key_image)
        status = AnonymousBallot.VERIFIED if reason is None else AnonymousBallot.REJECTED
        if ballot.verification_status != status:
            AnonymousBallot.objects.filter(pk=ballot.pk).update(verification_status=status)
        if reason is None:
            verified += 1
        else:
            rejected += 1
            issues.append({"ballot_id": str(ballot.id), "reason": reason})
    credentials = AuthorizationCredential.objects.filter(election=election, status=AuthorizationCredential.ACTIVE).count()
    chain = verify_chain()
    total = verified + rejected
    report = {
        "election_id": str(election.pk), "ballots_total": total, "ballots_verified": verified, "ballots_rejected": rejected,
        "credentials_active": credentials, "ring_size": len(ring_hex), "ring_hash": ring_h,
        "ballots_not_exceeding_credentials": total <= credentials, "audit_chain_ok": chain["ok"], "issues": issues,
    }
    report["passed"] = rejected == 0 and chain["ok"] and report["ballots_not_exceeding_credentials"]
    log_event("ELECTION_VERIFIED", election=election, actor=actor,
              details={k: v for k, v in report.items() if k != "issues"})
    return report
