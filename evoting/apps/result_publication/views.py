from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_management.services import log_event
from apps.common.exceptions import ApiError
from apps.common.integration import CLOSED, election_phase, get_election
from apps.common.views import PublicAPIView
from apps.result_calculation.models import ElectionResult


class PublishResultView(APIView):
    """POST /api/results/<election_id>/publish/   (admin)"""

    def post(self, request, election_id):
        election = get_election(election_id)
        result = ElectionResult.objects.filter(election=election).first()
        if result is None:
            raise ApiError("NO_RESULT", "Calculate the result first.", 409)
        if election_phase(election) != CLOSED:
            raise ApiError("ELECTION_NOT_CLOSED", "Election is not closed.", 409)
        if result.verification_status != ElectionResult.VERIFIED:
            raise ApiError("RESULT_NOT_VERIFIED", "Only verified results can be published.", 409)
        if result.published_at is None:
            result.published_at = timezone.now()
            result.save(update_fields=["published_at"])
            log_event("RESULT_PUBLISHED", election=election, actor=f"admin:{request.user.pk}")
        return Response({"published_at": result.published_at})


class PublicResultView(PublicAPIView):
    """GET /api/results/<election_id>/   (public, only after publication)"""

    def get(self, request, election_id):
        election = get_election(election_id)
        result = ElectionResult.objects.filter(election=election, published_at__isnull=False).first()
        if result is None:
            raise ApiError("RESULT_NOT_PUBLISHED", "Results have not been published yet.", 404)
        return Response({"election_id": str(election.pk), "published_at": result.published_at,
                         "valid_ballots": result.valid_ballots, "rejected_ballots": result.rejected_ballots,
                         "candidates": result.result_data["candidates"],
                         "aggregate_ciphertexts": result.result_data["aggregate_ciphertexts"]})
