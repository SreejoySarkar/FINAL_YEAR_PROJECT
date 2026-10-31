from rest_framework.response import Response

from apps.anonymous_authorization.services import get_ring_hex, ring_hash
from apps.common.exceptions import ApiError
from apps.common.integration import REGISTRATION, VOTING, election_phase, get_election
from apps.common.views import PublicAPIView
from apps.vote_encryption.services import get_active_key

from .services import build_ballot_definition


class BallotView(PublicAPIView):
    """GET /api/ballots/<election_id>/   (public)"""

    def get(self, request, election_id):
        election = get_election(election_id)
        phase = election_phase(election)
        if phase not in (REGISTRATION, VOTING):
            raise ApiError("BALLOT_UNAVAILABLE", "No ballot is available for this election phase.", 409)
        key = get_active_key(election)
        ring = get_ring_hex(election)
        definition = build_ballot_definition(election)
        return Response({
            "election_id": str(election.pk), "phase": phase,
            "options": definition["options"], "definition_hash": definition["hash"],
            "encryption": {"algorithm": key.algorithm, "public_key": key.public_key},
            "ring": {"size": len(ring), "ring_hash": ring_hash(ring),
                     "url": f"/api/anonymous-auth/ring/{election.pk}/"},
        })
