from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anonymous_authorization.models import AuthorizationCredential
from apps.anonymous_authorization.services import get_ring_hex, ring_hash
from apps.anonymous_storage.models import AnonymousBallot
from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.integration import REGISTRATION, election_phase, get_election
from apps.qr_validation.models import QRToken
from apps.voter_authorization.models import VoterEligibility


class AuthorizationSummaryView(APIView):
    """GET /api/authorization/<election_id>/summary/   (admin) - counts only, no voter<->key mapping exists."""

    def get(self, request, election_id):
        e = get_election(election_id)
        creds = AuthorizationCredential.objects.filter(election=e)
        ring = get_ring_hex(e)
        return Response({
            "election_id": str(e.pk), "phase": election_phase(e),
            "eligible_voters": VoterEligibility.objects.filter(election=e, is_eligible=True).count(),
            "qr_tokens_issued": QRToken.objects.filter(election=e).count(),
            "qr_tokens_used": QRToken.objects.filter(election=e, is_used=True).count(),
            "credentials_active": creds.filter(status=AuthorizationCredential.ACTIVE).count(),
            "credentials_revoked": creds.filter(status=AuthorizationCredential.REVOKED).count(),
            "ring_size": len(ring), "ring_hash": ring_hash(ring),
            "ballots_cast": AnonymousBallot.objects.filter(election=e).count(),
        })


class CredentialListView(APIView):
    """GET /api/authorization/<election_id>/credentials/   (admin)"""

    def get(self, request, election_id):
        e = get_election(election_id)
        rows = AuthorizationCredential.objects.filter(election=e).order_by("credential_reference")
        return Response([{"credential_reference": r.credential_reference, "status": r.status} for r in rows])


class RevokeCredentialView(APIView):
    """POST /api/authorization/credentials/<credential_reference>/revoke/   (admin, registration phase only)

    The ring is frozen once voting opens: changing it afterwards would invalidate every cast ballot."""

    def post(self, request, credential_reference):
        cred = AuthorizationCredential.objects.filter(credential_reference=credential_reference).select_related("election").first()
        if cred is None:
            raise ApiError("CREDENTIAL_NOT_FOUND", "Credential not found.", 404)
        if election_phase(cred.election) != REGISTRATION:
            raise ApiError("RING_FROZEN", "Credentials can only be revoked before voting starts.", 409)
        cred.status = AuthorizationCredential.REVOKED
        cred.save(update_fields=["status"])
        log_event("CREDENTIAL_REVOKED", election=cred.election, actor=f"admin:{request.user.pk}",
                  details={"credential_reference": credential_reference})
        return Response({"credential_reference": credential_reference, "status": cred.status})
