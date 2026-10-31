from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_management.services import log_event
from apps.common.integration import get_election

from .models import VoterEligibility
from .serializers import EligibilitySerializer, SyncSerializer
from .services import sync_eligibility


class SyncEligibilityView(APIView):
    """POST /api/voter-authorization/sync/  {"election_id": 1}   (admin)"""

    def post(self, request):
        data = SyncSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        election = get_election(data.validated_data["election_id"])
        added = sync_eligibility(election, actor=f"admin:{request.user.pk}")
        return Response({"election_id": str(election.pk), "added": added})


class EligibilityListView(ListAPIView):
    """GET /api/voter-authorization/eligibility/?election_id=1   (admin)"""

    serializer_class = EligibilitySerializer

    def get_queryset(self):
        qs = VoterEligibility.objects.all().order_by("id")
        if self.request.query_params.get("election_id"):
            qs = qs.filter(election_id=self.request.query_params["election_id"])
        return qs


class EligibilityUpdateView(UpdateAPIView):
    """PATCH /api/voter-authorization/eligibility/<id>/  {"is_eligible": false}   (admin)"""

    serializer_class = EligibilitySerializer
    queryset = VoterEligibility.objects.all()
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        row = serializer.save()
        log_event("ELIGIBILITY_CHANGED", election=row.election, actor=f"admin:{self.request.user.pk}",
                  details={"eligibility_id": row.pk, "is_eligible": row.is_eligible})
