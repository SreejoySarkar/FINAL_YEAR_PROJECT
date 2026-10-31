from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anonymous_storage.models import AnonymousBallot
from apps.common.integration import get_election
from apps.common.views import PublicAPIView

from .services import verify_election


class RunVerificationView(APIView):
    """POST /api/verification/<election_id>/run/   (admin; CPU heavy - move to a worker for big elections)"""

    def post(self, request, election_id):
        return Response(verify_election(get_election(election_id), actor=f"admin:{request.user.pk}"))


class PublicBallotListView(PublicAPIView, ListAPIView):
    """GET /api/verification/<election_id>/public-data/?limit=&offset=   (public)

    Everything an outside auditor needs to re-run the checks themselves."""

    def list(self, request, *args, **kwargs):
        election = get_election(kwargs["election_id"])
        qs = AnonymousBallot.objects.filter(election=election).order_by("id").prefetch_related("components")
        page = self.paginate_queryset(qs)
        rows = [{
            "ballot_id": str(b.id), "key_image": b.key_image, "verification_status": b.verification_status,
            "ciphertexts": [c.ciphertext for c in sorted(b.components.all(), key=lambda c: c.option_index)],
            "ring_signature": b.ring_signature, "proof_data": b.proof_data,
        } for b in page]
        return self.get_paginated_response(rows)
