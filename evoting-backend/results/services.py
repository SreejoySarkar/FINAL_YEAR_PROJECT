
import hmac
from collections import Counter

from cryptography.exceptions import InvalidTag

from audit.services import verify_chain, verify_after_checkpoint
from qrtokens.models import QRToken
from voters.models import Eligibility
from voting.crypto import decrypt_ballot, integrity_value
from voting.models import Ballot


def verify_election(election):
    """Verify election counts, ballot integrity and post-checkpoint audit records."""

    problems = []
    warnings = []

    ballots = Ballot.objects.filter(election=election)
    n_ballots = ballots.count()

    n_voted = Eligibility.objects.filter(
        election=election,
        has_voted=True
    ).count()

    n_used = QRToken.objects.filter(
        election=election,
        is_used=True
    ).count()

    if not (n_ballots == n_voted == n_used):
        problems.append(
            f"Counts disagree: ballots={n_ballots}, "
            f"voters marked voted={n_voted}, QR tokens used={n_used}"
        )

    bad = 0

    for b in ballots.iterator():
        expected = integrity_value(
            election.id,
            bytes(b.nonce),
            bytes(b.encrypted_ballot)
        )

        if not hmac.compare_digest(expected, b.integrity_hash):
            bad += 1

    if bad:
        problems.append(
            f"{bad} ballot(s) failed the integrity check"
        )

    # Check the complete historical audit chain.
    historical_chain_ok, first_bad = verify_chain()

    if not historical_chain_ok:
        warnings.append(
            f"Historical audit chain remains broken at record {first_bad}"
        )

    # Check audit records created after the recovery checkpoint.
    checkpoint_ok, checkpoint_issue = verify_after_checkpoint()

    if not checkpoint_ok:
        problems.append(
            f"Post-checkpoint audit verification failed: {checkpoint_issue}"
        )

    return {
        "ok": not problems,
        "ballots": n_ballots,
        "voters_marked_voted": n_voted,
        "tokens_used": n_used,
        "bad_integrity": bad,
        "audit_chain_intact": historical_chain_ok,
        "historical_first_bad_record_id": first_bad,
        "post_checkpoint_audit_intact": checkpoint_ok,
        "warnings": warnings,
        "problems": problems
    }


def _decrypt_all(election):
    if election.status != "closed":
        raise PermissionError(
            "Ballots can only be decrypted after the election is closed."
        )

    for b in Ballot.objects.filter(election=election).iterator():
        yield decrypt_ballot(
            election.id, bytes(b.nonce), bytes(b.encrypted_ballot)
        )


def tally(election):
    """First count: a plain loop."""
    counts = {c.id: 0 for c in election.candidates.all()}
    unknown = 0

    for cid in _decrypt_all(election):
        if cid in counts:
            counts[cid] += 1
        else:
            unknown += 1

    return counts, unknown


def independent_recount(election):
    """Second count: a different code path (decrypt all, then use Counter)."""
    ids = list(_decrypt_all(election))
    counter = Counter(ids)

    return {
        c.id: counter.get(c.id, 0)
        for c in election.candidates.all()
    }, len(ids)


def compute_result(election):
    """Verify, count twice, compare. Returns {'ok': bool, 'report': ..., 'data': ...}."""
    report = verify_election(election)

    if not report["ok"]:
        return {"ok": False, "report": report}

    try:
        counts, unknown = tally(election)
        recount, _ = independent_recount(election)
    except InvalidTag:
        report["ok"] = False
        report["problems"].append(
            "A ballot failed decryption (tampering or wrong key)"
        )
        return {"ok": False, "report": report}

    if unknown or counts != recount or sum(counts.values()) != report["ballots"]:
        report["ok"] = False
        report["problems"].append("Tally and independent recount disagree")
        return {"ok": False, "report": report}

    total = sum(counts.values())
    rows = []

    for c in election.candidates.order_by("id"):
        v = counts[c.id]
        rows.append({
            "candidate_id": c.id,
            "name": c.name,
            "votes": v,
            "percent": round(100 * v / total, 1) if total else 0
        })

    top = max(counts.values(), default=0)
    winners = [cid for cid, v in counts.items() if v == top] if total else []

    eligible = Eligibility.objects.filter(
        election=election, is_eligible=True
    ).count()

    return {
        "ok": True,
        "report": report,
        "data": {
            "tally": rows,
            "total_votes": total,
            "eligible_voters": eligible,
            "winner_ids": winners
        }
    }
