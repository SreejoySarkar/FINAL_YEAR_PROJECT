from django.conf import settings
from django.http import Http404
from rest_framework.response import Response

from apps.common.integration import election_phase, get_election
from apps.common.views import PublicAPIView
from evoting_crypto import lsag

from .serializers import IssueCredentialSerializer
from .services import get_ring_hex, issue_credential, pop_context, ring_hash


class IssueCredentialView(PublicAPIView):
    """POST /api/anonymous-auth/credentials/   (public; authorised by the QR token)

    {"token": "...", "public_key": "02ab...", "possession_proof": {"R": "02..", "s": ".."}}"""

    def post(self, request):
        data = IssueCredentialSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        cred = issue_credential(token=data.validated_data["token"], public_key_hex=data.validated_data["public_key"],
                                possession_proof=data.validated_data["possession_proof"])
        return Response({"credential_reference": cred.credential_reference,
                         "election_id": str(cred.election_id)}, status=201)


class RingView(PublicAPIView):
    """GET /api/anonymous-auth/ring/<election_id>/   (public) - the set voters sign over."""

    def get(self, request, election_id):
        election = get_election(election_id)
        keys = get_ring_hex(election)
        return Response({"election_id": str(election.pk), "phase": election_phase(election),
                         "size": len(keys), "ring_hash": ring_hash(keys), "public_keys": keys})


class DevKeypairView(PublicAPIView):
    """POST /api/anonymous-auth/dev/keypair/  {"election_id": 1}  - DEMO ONLY (ENABLE_DEMO_ENDPOINTS).

    The server sees the private key, which defeats anonymity. Real clients generate keys locally
    (see tools/voter_client.py)."""

    def post(self, request):
        if not settings.ENABLE_DEMO_ENDPOINTS:
            raise Http404
        election = get_election(request.data.get("election_id"))
        x, y = lsag.generate_keypair()
        return Response({"private_key": format(x, "x"), "public_key": y,
                         "possession_proof": lsag.prove_possession(x, pop_context(election.pk)),
                         "warning": "demo only - never generate keys on the server in production"})
