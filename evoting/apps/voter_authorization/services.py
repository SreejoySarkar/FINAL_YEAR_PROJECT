from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.integration import REGISTRATION, election_phase, is_voter_active, iter_active_voters

from .models import VoterEligibility


def authorize_voter(voter, election, *, phase=REGISTRATION, for_update=False) -> VoterEligibility:
    """Checks Person 1's voter/election records plus our eligibility table."""
    if not is_voter_active(voter):
        raise ApiError("VOTER_INACTIVE", "Voter account is not active.", 403)
    if election_phase(election) != phase:
        raise ApiError("ELECTION_PHASE_INVALID", f"Election is not in the '{phase}' phase.", 409)
    qs = VoterEligibility.objects.all()
    if for_update:
        qs = qs.select_for_update()
    row = qs.filter(voter=voter, election=election).first()
    if row is None or not row.is_eligible:
        raise ApiError("NOT_ELIGIBLE", "Voter is not eligible for this election.", 403)
    return row


def sync_eligibility(election, actor: str) -> int:
    existing = set(VoterEligibility.objects.filter(election=election).values_list("voter_id", flat=True))
    new = [VoterEligibility(voter=v, election=election, is_eligible=True) for v in iter_active_voters() if v.pk not in existing]
    VoterEligibility.objects.bulk_create(new, ignore_conflicts=True)
    log_event("ELIGIBILITY_SYNCED", election=election, actor=actor, details={"added": len(new)})
    return len(new)
