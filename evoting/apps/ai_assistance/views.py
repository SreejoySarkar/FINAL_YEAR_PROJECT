from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.integration import get_election

from .services import analyze_election


class AnomalyView(APIView):
    """GET /api/ai/anomalies/<election_id>/   (admin)"""

    def get(self, request, election_id):
        return Response(analyze_election(get_election(election_id)))
